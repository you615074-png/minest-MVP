from pydantic import BaseModel, Field
from utils.helpers import get_agent_llm
from core.state import AgentState


class EmailDraft(BaseModel):
    subject: str = Field(description="邮件主题行，必须引用目标公司具体近期事件，30字以内")
    body: str = Field(description="邮件正文，200字以内中文，真诚专业，不以'我'开头")
    ps_line: str = Field(description="PS附言，一句话补充说明或提供社会证明，50字以内")


def copywriter_node(state: AgentState) -> AgentState:
    """破冰文案专家：撰写个性化中文开发信"""
    logs = list(state.get("log_messages", []))
    logs.append("✍️ [文案专家] 开始撰写个性化开发信...")

    try:
        llm = get_agent_llm("COPYWRITER")
        from langchain_core.output_parsers import PydanticOutputParser
        parser = PydanticOutputParser(pydantic_object=EmailDraft)

        profile = state["company_profile"]
        hooks_text = "\n".join(
            f"- {h}" for h in state.get("key_hooks", [])
        )

        prompt = f"""你是一位顶级B2B销售文案专家，擅长撰写高打开率的开发信。
请严格使用【{state.get('language', '简体中文')}】撰写邮件，并且遵守以下规则：
1. 主题行：必须引用目标公司具体的近期动态（融资/产品发布/人员变动），不能泛泛而谈
2. 开头：不以"我"或"我们"开头，先聚焦对方视角和处境
3. 钩子：将对方具体痛点与我方方案自然连接，避免生硬的产品推销
4. CTA：只提一个低门槛行动（如"方便下周找个15分钟聊聊吗？"）
5. 长度：正文不超过200字
6. 语气：专业但不官腔，真诚不卑不亢

【目标公司信息】
公司名称：{profile.get('company_name')}
近期动态：{', '.join(profile.get('recent_news', ['暂无']))}
核心产品：{', '.join(profile.get('main_products', []))}
推断痛点：{', '.join(profile.get('pain_points_inferred', []))}
融资阶段：{profile.get('funding_stage', '未知')}

【我方产品卖点】
{state['product_desc']}

【核心销售切入点（参考使用）】
{hooks_text}

【评分依据（了解背景）】
{state.get('score_rationale', '')}

请生成一封能让对方有共鸣、想回复的开发信。

{parser.get_format_instructions()}"""

        response = llm.invoke(prompt)
        result: EmailDraft = parser.parse(response.content)

        logs.append("✍️ [文案专家] ✅ 开发信草稿生成完成")
        logs.append(f"✍️ [文案专家] 主题：{result.subject}")

        return {
            **state,
            "email_draft": result.model_dump(),
            "log_messages": logs,
        }

    except Exception as e:
        logs.append(f"✍️ [文案专家] ❌ 文案生成失败：{str(e)[:100]}")
        return {
            **state,
            "error_message": f"文案生成失败：{str(e)}",
            "log_messages": logs,
        }
