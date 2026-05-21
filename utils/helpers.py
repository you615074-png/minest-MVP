import os
from langchain_openai import ChatOpenAI
from core import AGENT_TEMPERATURES


def get_llm(provider: str, temperature: float = 0.0) -> ChatOpenAI:
    p = provider.upper()
    api_key = os.getenv(f"{p}_API_KEY", "")
    base_url = os.getenv(f"{p}_BASE_URL", "")
    model = os.getenv(f"{p}_MODEL", "")

    if not api_key:
        raise ValueError(f"未找到 {p}_API_KEY，请在 .env 文件中填写。")
    if not model:
        raise ValueError(f"未找到 {p}_MODEL，请在 .env 文件中填写模型名称。")

    return ChatOpenAI(
        api_key=api_key,
        base_url=base_url or None,
        model=model,
        temperature=temperature,
        request_timeout=60,
        max_retries=2,
    )


def get_agent_llm(agent_role: str) -> ChatOpenAI:
    provider = os.getenv(f"{agent_role.upper()}_PROVIDER", "deepseek")
    temp = AGENT_TEMPERATURES.get(agent_role, AGENT_TEMPERATURES.get(agent_role.lower(), 0.0))
    return get_llm(provider, temperature=temp)
