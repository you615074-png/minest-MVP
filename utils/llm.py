"""
统一 LLM 调用工具 — 结构化输出解析 + 自动注入 JSON Schema + 格式纠错重试。
"""
from langchain_core.output_parsers import PydanticOutputParser


def invoke_structured(llm, prompt: str, pydantic_model, max_retries: int = 2):
    """
    调用 LLM 并解析为 Pydantic 模型。

    自动注入 PydanticOutputParser 的 JSON Schema。
    若解析失败则追加纠正指令后重试（最多 max_retries 次）。
    """
    parser = PydanticOutputParser(pydantic_object=pydantic_model)
    format_instructions = parser.get_format_instructions()

    base_prompt = (
        f"{prompt}\n\n{format_instructions}"
        "\n\n输出要求：所有字段必须填充真实内容，不得输出空字符串或占位符。"
    )

    for attempt in range(max_retries + 1):
        response = llm.invoke(base_prompt)
        try:
            return parser.parse(response.content)
        except Exception as e:
            if attempt == max_retries:
                raise
            err_detail = str(e)
            if len(err_detail) > 200:
                err_detail = err_detail[:200]
            base_prompt = (
                base_prompt
                + f"\n\n【系统指令】验证错误：{err_detail}。请修正上述具体问题后重新输出。只输出 JSON 对象，不要包含 markdown 代码块标记。"
            )
    return None
