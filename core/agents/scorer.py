"""
商机打分员 — 四维固定档位评分 + Pydantic 自动校正。
"""
from pydantic import BaseModel, Field, model_validator
from utils.helpers import get_agent_llm
from utils.llm import invoke_structured
from core.state import AgentState
from core import RECOVERABLE_ERRORS, AgentRole
from utils.logger import logger

# 有效分数档位（LLM 只能在以下值中选择）
VALID_TIERS = {
    "industry_score": (0, 15, 25),
    "pain_point_score": (0, 20, 35),
    "size_score": (0, 10, 20),
    "timing_score": (0, 10, 20),
}


def _snap_to_tier(value: int, tiers: tuple[int, ...]) -> int:
    """将任意整数靠拢到最近的有效档位"""
    return min(tiers, key=lambda t: abs(t - value))


def _validate_sub_score(value: int, tiers: tuple[int, ...]) -> int:
    if value in tiers:
        return value
    return _snap_to_tier(value, tiers)


class LeadScore(BaseModel):
    industry_score: int = Field(description="行业匹配度得分——只能选 0 / 15 / 25")
    pain_point_score: int = Field(description="痛点契合度得分——只能选 0 / 20 / 35")
    size_score: int = Field(description="规模适配度得分——只能选 0 / 10 / 20")
    timing_score: int = Field(description="时机成熟度得分——只能选 0 / 10 / 20")
    score: int = Field(description="综合评分，必须等于四项之和", ge=0, le=100)
    rationale: str = Field(description="评分依据，150字以内，需引用公司具体特征")
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
            logger.info(
                f"[SCORER] 自动校正评分: {corrections}"
            )
        return self


def scorer_node(state: AgentState) -> AgentState:
    logs = list(state.get("log_messages", []))

    if state.get("error_message"):
        return state

    log_msg = f"[{AgentRole.SCORER}] 开始评估商机质量..."
    logs.append(log_msg)
    logger.info(log_msg)

    try:
        llm = get_agent_llm("SCORER")
        profile = state["company_profile"]
        prompt = f"""你是一位经验丰富的B2B销售顾问，请评估这条销售线索的质量。

【我方产品卖点】
{state['product_desc']}

【理想客户画像 (ICP)】
{state['icp_definition']}

【目标公司档案】
公司：{profile.get('company_name')} | 行业：{profile.get('industry')} | 规模：{profile.get('company_size')}
融资阶段：{profile.get('funding_stage')}
核心产品：{', '.join(profile.get('main_products', []))}
近期动态：{', '.join(profile.get('recent_news', []))}
推断痛点：{', '.join(profile.get('pain_points_inferred', []))}

请严格按以下四个维度的【固定档位】评分，每个维度只能从给定选项中选择一个整数：
1. industry_score: 只能选 {VALID_TIERS['industry_score']}
2. pain_point_score: 只能选 {VALID_TIERS['pain_point_score']}
3. size_score: 只能选 {VALID_TIERS['size_score']}
4. timing_score: 只能选 {VALID_TIERS['timing_score']}

score 必须等于上述四项之和。
即使你觉得某个值"接近"也对，系统会自动修正到最近的有效档位。请优先确保你的判断逻辑自洽。
"""

        result: LeadScore = invoke_structured(llm, prompt, LeadScore)
        should_proceed = result.score > 60

        log_msg = f"[{AgentRole.SCORER}] ✅ 评分完成：{result.score}/100  (行业{result.industry_score}+痛点{result.pain_point_score}+规模{result.size_score}+时机{result.timing_score})"
        logs.append(log_msg)
        logger.info(log_msg)
        logs.append(f"[{AgentRole.SCORER}] 依据：{result.rationale[:80]}...")

        if should_proceed:
            logs.append(f"[{AgentRole.SCORER}] ✅ 评分合格（>60），移交文案专家")
            logger.info(log_msg)
        else:
            logs.append(f"[{AgentRole.SCORER}] ⛔ 评分不足60分，终止流程，节省 API 成本")
            logger.info(log_msg)

        return {
            **state,
            "lead_score": result.score,
            "score_rationale": result.rationale,
            "key_hooks": result.key_hooks,
            "should_proceed": should_proceed,
            "log_messages": logs,
        }

    except RECOVERABLE_ERRORS as e:
        log_msg = f"[{AgentRole.SCORER}] ❌ 评分失败：{str(e)[:100]}"
        logs.append(log_msg)
        logger.error(log_msg)
        return {
            **state,
            "error_message": f"评分失败：{str(e)}",
            "log_messages": logs,
        }
