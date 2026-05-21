"""
商机打分员 — 四维 × 5 档评分 + 证据锚定 + Pydantic 自动校正。
每次 LLM 输出后 model_validator 自动将子分靠拢到最近有效档位并修正总分，
消除「同一输入得 40 分 vs 75 分」的不确定性。
"""
from pydantic import BaseModel, Field, model_validator
from utils.helpers import get_agent_llm
from utils.llm import invoke_structured
from core.state import AgentState
from core import RECOVERABLE_ERRORS, AgentRole
from utils.logger import logger

VALID_TIERS = {
    "industry_score": (0, 6, 12, 18, 25),
    "pain_point_score": (0, 9, 17, 26, 35),
    "size_score": (0, 5, 10, 15, 20),
    "timing_score": (0, 5, 10, 15, 20),
}

TIER_LABELS = {
    "industry_score": ("完全不相关", "微弱关联", "边缘行业", "主要行业", "核心定位"),
    "pain_point_score": ("无吻合", "1个模糊", "1个明确", "2个明确", "3+完美"),
    "size_score": ("超出范围", "信息未知", "边界适配", "基本匹配", "最佳区间"),
    "timing_score": ("负面动态", "无动态", "中性信号", "间接利好", "直接信号"),
}


def _snap_to_tier(value: int, tiers: tuple[int, ...]) -> int:
    return min(tiers, key=lambda t: abs(t - value))


def _tier_index(value: int, tiers: tuple[int, ...]) -> int:
    return tiers.index(_snap_to_tier(value, tiers))


def _validate_sub_score(value: int, tiers: tuple[int, ...]) -> int:
    return value if value in tiers else _snap_to_tier(value, tiers)


class LeadScore(BaseModel):
    industry_score: int = Field(description="行业匹配度，只能选 0/6/12/18/25")
    industry_evidence: str = Field(description="引述公司行业/主营产品原文，论证为什么选该档位（1句话）")
    pain_point_score: int = Field(description="痛点契合度，只能选 0/9/17/26/35")
    pain_point_evidence: str = Field(description="引述推断痛点原文，论证与我方产品的吻合程度（1句话）")
    size_score: int = Field(description="规模适配度，只能选 0/5/10/15/20")
    size_evidence: str = Field(description="引述公司规模/融资阶段原文，论证与ICP的匹配程度（1句话）")
    timing_score: int = Field(description="时机成熟度，只能选 0/5/10/15/20")
    timing_evidence: str = Field(description="引述近期新闻/动态原文，论证当前是否存在采购信号（1句话）")
    score: int = Field(description="综合评分 = 四维校正后之和", ge=0, le=100)
    rationale: str = Field(description="整体判断依据，150字以内引用公司具体特征")
    key_hooks: list[str] = Field(description="销售切入点，2-3条，每条20字以内")

    @model_validator(mode="after")
    def enforce_scoring_rules(self):
        corrections = {}
        for field_name, tiers in VALID_TIERS.items():
            raw = getattr(self, field_name)
            corrected = _validate_sub_score(raw, tiers)
            if corrected != raw:
                corrections[field_name] = (raw, corrected)
                setattr(self, field_name, corrected)

        computed = (
            self.industry_score
            + self.pain_point_score
            + self.size_score
            + self.timing_score
        )
        if self.score != computed:
            corrections["score"] = (self.score, computed)
            self.score = computed

        if corrections:
            logger.info(f"[SCORER] 自动校正: {corrections}")
        return self


def _build_tier_table() -> str:
    lines = []
    for dim, tiers in VALID_TIERS.items():
        labels = TIER_LABELS[dim]
        dim_cn = {
            "industry_score": "行业匹配度",
            "pain_point_score": "痛点契合度",
            "size_score": "规模适配度",
            "timing_score": "时机成熟度",
        }[dim]
        row = " | ".join(
            f"{score}分={label}" for score, label in zip(tiers, labels)
        )
        lines.append(f"{dim_cn}: {row}")
    return "\n".join(lines)


def scorer_node(state: AgentState) -> AgentState:
    logs = list(state.get("log_messages", []))

    if state.get("error_message"):
        return state

    log_msg = f"[{AgentRole.SCORER}] 开始评估商机质量（5档 × 4维）..."
    logs.append(log_msg)
    logger.info(log_msg)

    try:
        llm = get_agent_llm("SCORER")
        profile = state["company_profile"]
        raw_data_len = len(state.get("company_raw_data", ""))
        low_data = raw_data_len < 200 or not profile.get("company_name")

        if low_data:
            logger.warning(f"[SCORER] 原始数据不足({raw_data_len}字符)，降级为宽松评分")
            logs.append(f"[{AgentRole.SCORER}] ⚠️ 目标公司信息不足，使用行业常识推断")

        mode_hint = (
            "⚠️ 目标公司档案信息严重不足。如果某维度确实没有任何可引述的事实，请在 evidence 字段中填写「信息不足，(推断)」然后选择 Tier 1（最低非零档）。\n"
            if low_data
            else ""
        )

        prompt = f"""你是 B2B 销售线索评分专家。请先读目标公司档案，再逐维给出证据和分数。

【我方产品】
{state['product_desc']}

【ICP 画像】
{state['icp_definition']}

【目标公司档案】
公司={profile.get('company_name')} | 行业={profile.get('industry')} | 规模={profile.get('company_size')}
融资={profile.get('funding_stage')}
核心产品={', '.join(profile.get('main_products', []))}
近期动态={', '.join(profile.get('recent_news', []))}
推断痛点={', '.join(profile.get('pain_points_inferred', []))}

============================================================
【四维 × 5 档评分表】每个维度的分数只能从该行的固定值中选择：
============================================================
{_build_tier_table()}
============================================================

【信息缺失处理规则】
如果目标公司档案中某字段为"未知"或空值，该维度的子分取其中间档位：
  - 行业为"未知" → 选 12（边缘行业，给中间分）
  - 规模/融资为"未知" → 选 10
  - 近期动态为空/非采购信号 → 选 10
  - evidence 字段填写"档案中该项为未知，取中性评分"

痛点判据：看产品功能是否吻合，不因措辞泛化而降档。
只要公司实际业务与产品功能能自然连接→选 Tier 2 或以上（≥1个明确吻合）。

【两步法评分流程】
第一步：对每个维度，从档案中引述一句事实作为证据。
第二步：根据证据，从对应行的固定值中选择最匹配的分数。
{mode_hint}
evidence 必须优先引用档案中已有原文。仅完全无信息时才标「(推断)」。
score 必须等于四维分数之和。"""

        result: LeadScore = invoke_structured(llm, prompt, LeadScore)
        should_proceed = result.score > 60

        log_msg = (
            f"[{AgentRole.SCORER}] ✅ {result.score}/100  "
            f"行业{result.industry_score}({result.industry_evidence[:20]}…) "
            f"+痛点{result.pain_point_score}({result.pain_point_evidence[:20]}…) "
            f"+规模{result.size_score}({result.size_evidence[:20]}…) "
            f"+时机{result.timing_score}({result.timing_evidence[:20]}…)"
        )
        logs.append(log_msg)
        logger.info(log_msg)

        if should_proceed:
            logs.append(f"[{AgentRole.SCORER}] ✅ ≥60分，移交文案专家")
        else:
            logs.append(f"[{AgentRole.SCORER}] ⛔ <60分，终止以节省 API")

        return {
            **state,
            "lead_score": result.score,
            "score_rationale": result.rationale,
            "key_hooks": result.key_hooks,
            "should_proceed": should_proceed,
            "log_messages": logs,
        }

    except RECOVERABLE_ERRORS as e:
        log_msg = f"[{AgentRole.SCORER}] ❌ 失败：{str(e)[:100]}"
        logs.append(log_msg)
        logger.error(log_msg)
        return {
            **state,
            "error_message": f"评分失败：{str(e)}",
            "log_messages": logs,
        }
