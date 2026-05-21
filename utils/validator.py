import os


def validate_config():
    errors = []
    warnings = []

    providers = ["DEEPSEEK", "KIMI", "MINIMAX"]
    configured = 0

    for p in providers:
        has_key = bool(os.getenv(f"{p}_API_KEY"))
        has_model = bool(os.getenv(f"{p}_MODEL"))
        if has_key and has_model:
            configured += 1
        elif has_key and not has_model:
            warnings.append(f"{p}_MODEL 未设置")
        elif not has_key and has_model:
            warnings.append(f"{p}_API_KEY 未设置")

    if configured == 0:
        errors.append("至少需要配置一个 LLM Provider（DEEPSEEK / KIMI / MINIMAX）")

    if not os.getenv("TAVILY_API_KEY"):
        warnings.append("TAVILY_API_KEY 未设置，新闻搜索功能将跳过")

    return errors, warnings
