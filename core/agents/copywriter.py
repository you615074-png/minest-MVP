from pydantic import BaseModel, Field
from utils.helpers import get_agent_llm
from utils.llm import invoke_structured
from core.state import AgentState
from core import RECOVERABLE_ERRORS, AgentRole
from utils.logger import logger


class EmailDraft(BaseModel):
    subject: str = Field(description="邮件主题行，必须引用目标公司具体近期事件，30字以内", min_length=5)
    body: str = Field(description="邮件正文，50-200字中文，真诚专业，不以'我'开头", min_length=10)
    ps_line: str = Field(description="PS附言，一句话补充说明或提供社会证明，50字以内")


def copywriter_node(state: AgentState) -> AgentState:
    logs = list(state.get("log_messages", []))
    log_msg = f"[{AgentRole.COPYWRITER}] 开始撰写个性化开发信..."
    logs.append(log_msg)
    logger.info(log_msg)

    try:
        llm = get_agent_llm("COPYWRITER")

        profile = state["company_profile"]
        hooks_text = "\n".join(
            f"- {h}" for h in state.get("key_hooks", [])
        )

        prompt = f"""你是一位顶级B2B销售文案专家，擅长撰写高打开率的开发信。
请严格使用【{state.get('language', '简体中文')}】撰写邮件，并且遵守以下规则：
1. 主题行：必须引用目标公司具体的近期动态（融资/产品发布/人员变动），不能泛泛而谈
2. 开头：不以"我"或"我们"开头，先聚焦对方视角和处境
3. 钩子：将对方具体痛点与我方方案自然连接，避免生硬的产品推销
4. CTA：只提一个低门槛行动
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

请生成一封能让对方有共鸣、想回复的开发信。务必填写完整的 body 字段（100-200字），不得留空或输出占位符。
"""

        result: EmailDraft = invoke_structured(llm, prompt, EmailDraft)
        company = profile.get("company_name", "贵司")

        body = result.body
        if not body or len(body.strip()) < 10:
            hooks = state.get("key_hooks", [])
            body = (
                f"关注到{company}近期发展动态，我司产品在"
                f"{', '.join(hooks[:2]) if hooks else '效率提升'}方面"
                f"可提供针对性合作方案。方便约15分钟简短沟通吗？"
            )
            logger.warning(f"[COPYWRITER] body为空，使用备用正文")
        if not body or len(body.strip()) < 5:
            body = f"尊敬的联系人，关注{company}的近期动态，我司产品与贵司业务高度匹配，期待进一步沟通。方便约个简短电话吗？"
            logger.warning(f"[COPYWRITER] body极短，使用最终兜底正文")

        draft = result.model_dump()
        if body != draft.get("body"):
            draft["body"] = body

        log_msg = f"[{AgentRole.COPYWRITER}] ✅ 开发信草稿生成完成"
        logs.append(log_msg)
        logger.info(log_msg)
        logs.append(f"[{AgentRole.COPYWRITER}] 主题：{draft['subject']}")

        return {
            **state,
            "email_draft": draft,
            "log_messages": logs,
        }

    except RECOVERABLE_ERRORS as e:
        log_msg = f"[{AgentRole.COPYWRITER}] ❌ 文案生成失败：{str(e)[:100]}"
        logs.append(log_msg)
        logger.error(log_msg)
        return {
            **state,
            "error_message": f"文案生成失败：{str(e)}",
            "log_messages": logs,
        }
