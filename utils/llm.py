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

    base_prompt = f"{prompt}\n\n{format_instructions}"

    for attempt in range(max_retries + 1):
        response = llm.invoke(base_prompt)
        try:
            return parser.parse(response.content)
        except Exception:
            if attempt == max_retries:
                raise
            base_prompt = (
                base_prompt
                + "\n\n【系统指令】上一次输出格式不合法，请严格按照以上 JSON Schema 重新输出。只输出 JSON 对象，不要包含任何额外文字或 markdown 代码块标记。"
            )
    return None
