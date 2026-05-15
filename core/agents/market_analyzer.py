from pydantic import BaseModel, Field
from utils.helpers import get_agent_llm
from core.state import AgentState


class TargetPersona(BaseModel):
    persona_name: str = Field(description="目标受众群体名称，如'中大型SaaS企业HR总监'")
    pain_points: list[str] = Field(description="该群体面临的具体痛点，2-3条")
    why_fit: str = Field(description="为什么我们的产品适合他们，解决什么核心问题")


class TargetCompany(BaseModel):
    company_name: str = Field(description="潜在公司名称")
    company_url: str = Field(description="该公司极有可能的官方网址（如 https://www.feishu.cn），请基于常识推测真实的官网")
    reason: str = Field(description="深度分析为什么推荐这家公司作为目标客户，结合他们的业务场景进行说明")


class MarketAnalysis(BaseModel):
    personas: list[TargetPersona] = Field(description="列出 1-2 个最核心的目标画像即可，不要过多")
    market_insights: str = Field(description="整体市场切入建议与销售策略，100字以内")
    potential_targets: list[TargetCompany] = Field(description="精确寻找 5 家具体的潜在客户公司名单，不可多也不可少")


def market_analyzer_node(state: AgentState) -> AgentState:
    """市场分析专家：在无目标 URL 时，基于产品卖点进行受众分析"""
    logs = list(state.get("log_messages", []))
    logs.append("🧠 [市场分析专家] 开始基于产品卖点进行受众市场推演...")

    try:
        llm = get_agent_llm("ANALYZER")
        from langchain_core.output_parsers import PydanticOutputParser
        parser = PydanticOutputParser(pydantic_object=MarketAnalysis)

        prompt = f"""你是一位顶级的 B2B 商业战略专家与市场分析师。
请严格使用【{state.get('language', '简体中文')}】输出分析结果。

用户目前没有指定特定的目标公司，希望你根据他们提供的【产品卖点】和【理想客户画像(ICP)参考】，
预测并分析最有可能购买该产品的 1-2 类核心客户群体（Buyer Personas），并给出精简的销售切入建议。
最重要的是，分析完成后，请精确寻找 5 家极有可能成为高意向客户的【具体公司】（无需多找，5家即可），列出他们的网址，并简要分析为什么他们需要这个产品。

【我方产品卖点】
{state.get('product_desc', '未知')}

【ICP 补充描述（如有）】
{state.get('icp_definition', '无')}

请深入思考产品的核心价值主张，匹配到现实世界中具体的行业、公司规模和业务场景。
输出格式必须严格遵循以下 JSON 结构：

{parser.get_format_instructions()}"""

        response = llm.invoke(prompt)
        result: MarketAnalysis = parser.parse(response.content)

        logs.append("🧠 [市场分析专家] ✅ 市场受众分析完成")
        for persona in result.personas:
            logs.append(f"🧠 [市场分析专家] 识别出核心受众: {persona.persona_name}")

        return {
            **state,
            "mode": "MARKET_ANALYSIS",
            "market_analysis": result.model_dump(),
            "log_messages": logs,
        }

    except Exception as e:
        logs.append(f"🧠 [市场分析专家] ❌ 分析失败：{str(e)[:100]}")
        return {
            **state,
            "mode": "MARKET_ANALYSIS",
            "error_message": f"市场分析失败：{str(e)}",
            "log_messages": logs,
        }
