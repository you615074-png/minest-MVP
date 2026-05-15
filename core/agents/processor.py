from pydantic import BaseModel, Field
from utils.helpers import get_agent_llm
from core.state import AgentState


class CompanyProfile(BaseModel):
    company_name: str = Field(description="公司名称")
    industry: str = Field(description="所属行业")
    company_size: str = Field(description="公司规模（人数区间或发展阶段）")
    main_products: list[str] = Field(description="核心产品或服务，3-5条")
    recent_news: list[str] = Field(description="近期重要动态或新闻，2-3条")
    funding_stage: str = Field(description="融资阶段，如天使轮/A轮/上市/未知")
    pain_points_inferred: list[str] = Field(description="根据信息推断出的业务痛点，2-4条")
    tech_stack_mentioned: list[str] = Field(description="提及的技术栈或工具，没有则返回空列表")


def processor_node(state: AgentState) -> AgentState:
    """数据处理器：将原始情报结构化为公司档案 JSON"""
    logs = list(state.get("log_messages", []))

    if state.get("error_message"):
        return state

    logs.append("⚙️ [处理器] 开始结构化提取公司信息...")

    try:
        llm = get_agent_llm("PROCESSOR")
        from langchain_core.output_parsers import PydanticOutputParser
        parser = PydanticOutputParser(pydantic_object=CompanyProfile)

        prompt = f"""你是一个商业信息提取专家。请从以下原始文本中提取关键商业信息。
目标公司官网网址为：{state['target_url']}

【重要指令】
1. 请务必确保你提取的 `company_name` 是【拥有该官网的主体公司】，绝不能是新闻中顺带提及的投资方、合作伙伴或个人（例如不能把投资人名字当作公司名）。
2. 若某项信息未明确提及，请根据上下文合理推断，无法推断则严格填"未知"。
3. 确保 pain_points_inferred 中的痛点与该公司实际业务强相关。

【原始文本】
{state['company_raw_data']}

{parser.get_format_instructions()}"""

        response = llm.invoke(prompt)
        profile: CompanyProfile = parser.parse(response.content)
        profile_dict = profile.model_dump()

        logs.append(
            f"⚙️ [处理器] ✅ 识别公司：{profile_dict['company_name']} "
            f"| 行业：{profile_dict['industry']} "
            f"| 融资：{profile_dict['funding_stage']}"
        )

        return {
            **state,
            "company_profile": profile_dict,
            "log_messages": logs,
        }

    except Exception as e:
        logs.append(f"⚙️ [处理器] ❌ 处理失败：{str(e)[:100]}")
        return {
            **state,
            "error_message": f"数据处理失败：{str(e)}",
            "log_messages": logs,
        }
