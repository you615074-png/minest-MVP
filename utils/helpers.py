import os
from langchain_openai import ChatOpenAI


def get_llm(provider: str, temperature: float = 0.0) -> ChatOpenAI:
    """根据 provider 名称从环境变量构建 LLM 客户端（OpenAI 兼容 API）"""
    p = provider.upper()
    api_key = os.getenv(f"{p}_API_KEY", "")
    base_url = os.getenv(f"{p}_BASE_URL", "")
    model = os.getenv(f"{p}_MODEL", "")

    if not api_key:
        raise ValueError(
            f"未找到 {p}_API_KEY，请在 .env 文件中填写。"
        )
    if not model:
        raise ValueError(
            f"未找到 {p}_MODEL，请在 .env 文件中填写模型名称。"
        )

    return ChatOpenAI(
        api_key=api_key,
        base_url=base_url or None,
        model=model,
        temperature=temperature,
    )


def get_agent_llm(agent_role: str) -> ChatOpenAI:
    """根据 Agent 角色名获取对应 LLM（角色 → provider → LLM）
    
    例：get_agent_llm("PROCESSOR") 读取 PROCESSOR_PROVIDER=qwen，
    再用 qwen 的 Key/URL/Model 构建客户端。
    """
    provider = os.getenv(f"{agent_role.upper()}_PROVIDER", "deepseek")
    
    # 根据业务要求严格约束 Temperature，保证一致性
    if agent_role.upper() in ["PROCESSOR", "SCORER", "ANALYZER"]:
        # 结构化提取和打分要求绝对严谨和可控，设为 0.0
        temp = 0.0
    elif agent_role.upper() == "COPYWRITER":
        # 商业文案需要一点连贯性，但为了防止胡言乱语，控制在 0.2
        temp = 0.2
    else:
        temp = 0.0
        
    return get_llm(provider, temperature=temp)
