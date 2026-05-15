from pydantic import BaseModel, Field
from utils.helpers import get_agent_llm
from core.state import AgentState


class LeadScore(BaseModel):
    industry_score: int = Field(description="行业匹配度得分 (0-25)")
    pain_point_score: int = Field(description="痛点契合度得分 (0-35)")
    size_score: int = Field(description="规模适配度得分 (0-20)")
    timing_score: int = Field(description="时机成熟度得分 (0-20)")
    score: int = Field(description="综合评分，必须等于上方四项得分之和", ge=0, le=100)
    rationale: str = Field(description="详细的评分依据，150字以内，需引用公司具体特征及扣分点")
    key_hooks: list[str] = Field(description="最重要的销售切入点，2-3条，每条20字以内")


def scorer_node(state: AgentState) -> AgentState:
    """商机打分员：对比 ICP 评分，决定是否继续生成文案"""
    logs = list(state.get("log_messages", []))

    if state.get("error_message"):
        return state

    logs.append("📊 [打分员] 开始评估商机质量...")

    try:
        llm = get_agent_llm("SCORER")
        from langchain_core.output_parsers import PydanticOutputParser
        parser = PydanticOutputParser(pydantic_object=LeadScore)

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

请严格按以下四个维度的【固定档位】进行选择打分（绝不能给出规定档位之外的分数）：

1. 行业匹配度（满分25）：
   - 25分：目标行业完全属于产品适用行业。
   - 15分：产品普适性强，边缘行业也有潜在需求。
   - 0分：完全不相干且无可能。

2. 痛点契合度（满分35）：
   - 35分：公司存在至少两个推断痛点与产品高度吻合。
   - 20分：只有一个痛点吻合，或痛点较模糊但业务有关联。
   - 0分：完全没有吻合的痛点。

3. 规模适配度（满分20）：
   - 20分：明确在理想客户(ICP)的规模范围内。
   - 10分：规模信息“未知”或缺失。
   - 0分：明确超出或低于 ICP 规模范围。

4. 时机成熟度（满分20）：
   - 20分：近期有明确的扩张、融资或产品发布等利好动态。
   - 10分：无明显动态，或仅有中性动态。
   - 0分：有明显的负面动态（如裁员、倒闭）。

【重要】你的 final `score` 必须严格等于上述四项之和。
请务必深思熟虑，确保相同的输入始终输出相同的分数。

{parser.get_format_instructions()}"""

        response = llm.invoke(prompt)
        result: LeadScore = parser.parse(response.content)
        should_proceed = result.score > 60

        logs.append(f"📊 [打分员] ✅ 评分完成：{result.score}/100")
        logs.append(f"📊 [打分员] 依据：{result.rationale[:60]}...")

        if should_proceed:
            logs.append("📊 [打分员] ✅ 评分合格（>60），移交文案专家")
        else:
            logs.append("📊 [打分员] ⛔ 评分不足60分，终止流程，节省 API 成本")

        return {
            **state,
            "lead_score": result.score,
            "score_rationale": result.rationale,
            "key_hooks": result.key_hooks,
            "should_proceed": should_proceed,
            "log_messages": logs,
        }

    except Exception as e:
        logs.append(f"📊 [打分员] ❌ 评分失败：{str(e)[:100]}")
        return {
            **state,
            "error_message": f"评分失败：{str(e)}",
            "log_messages": logs,
        }
