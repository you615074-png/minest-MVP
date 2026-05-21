from langchain_core.output_parsers import PydanticOutputParser


def invoke_structured(llm, prompt: str, pydantic_model, max_retries: int = 2):
    parser = PydanticOutputParser(pydantic_object=pydantic_model)

    for attempt in range(max_retries + 1):
        response = llm.invoke(prompt)
        try:
            return parser.parse(response.content)
        except Exception:
            if attempt == max_retries:
                raise
            prompt = (
                prompt
                + "\n\n【系统指令】上一次输出格式不合法，请严格按照以下 JSON Schema 重新输出，只输出 JSON，不要任何额外文字。"
            )
    return None
