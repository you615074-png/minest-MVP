import os
import requests
from core.state import AgentState
from core import RECOVERABLE_ERRORS, AgentRole
from utils.retry import retry
from utils.logger import logger


@retry(max_attempts=2, base_delay=1.0, exceptions=(requests.RequestException, TimeoutError, ConnectionError))
def _fetch_jina(url: str) -> str:
    jina_url = f"https://r.jina.ai/{url}"
    headers = {"Accept": "text/plain"}
    jina_key = os.getenv("JINA_API_KEY", "")
    if jina_key:
        headers["Authorization"] = f"Bearer {jina_key}"

    resp = requests.get(jina_url, headers=headers, timeout=20)
    if resp.status_code == 200 and len(resp.text) > 200:
        return resp.text[:2500]
    return ""


@retry(max_attempts=2, base_delay=1.0, exceptions=(requests.RequestException, TimeoutError, ConnectionError))
def _search_tavily(domain: str, company: str) -> list[str]:
    tavily_key = os.getenv("TAVILY_API_KEY", "")
    if not tavily_key:
        return []

    from tavily import TavilyClient
    client = TavilyClient(api_key=tavily_key)
    results = client.search(
        query=f'"{company}" AND (公司 OR 融资 OR 业务介绍 OR 产品) site:{domain}',
        max_results=3,
        search_depth="advanced",
    )

    if not results.get("results"):
        results = client.search(
            query=f'"{company}" (融资 OR 新闻 OR 产品发布)',
            max_results=4,
        )

    items = results.get("results", [])
    return [f"- {r['title']}: {r.get('content', '')[:200]}" for r in items]


def researcher_node(state: AgentState) -> AgentState:
    logs = list(state.get("log_messages", []))
    url = state["target_url"]
    log_msg = f"[{AgentRole.RESEARCHER}] 开始分析目标：{url}"
    logs.append(log_msg)
    logger.info(log_msg)

    raw_data = ""

    try:
        page_text = _fetch_jina(url)
        if page_text:
            raw_data += f"【官网内容】\n{page_text}\n\n"
            log_msg = f"[{AgentRole.RESEARCHER}] ✅ 官网抓取成功（{len(page_text)} 字符）"
            logs.append(log_msg)
            logger.info(log_msg)
        else:
            log_msg = f"[{AgentRole.RESEARCHER}] ⚠️ 官网内容不足，将用搜索结果补充"
            logs.append(log_msg)
            logger.warning(log_msg)
    except RECOVERABLE_ERRORS as e:
        log_msg = f"[{AgentRole.RESEARCHER}] ⚠️ 官网抓取失败：{str(e)[:60]}，转用搜索"
        logs.append(log_msg)
        logger.warning(log_msg)

    try:
        domain = url.replace("https://", "").replace("http://", "").split("/")[0]
        company = domain.replace("www.", "").split(".")[0]
        news_lines = _search_tavily(domain, company)

        if news_lines:
            raw_data += "【近期新闻与动态】\n" + "\n".join(news_lines) + "\n"
            log_msg = f"[{AgentRole.RESEARCHER}] ✅ 搜索到 {len(news_lines)} 条相关动态"
            logs.append(log_msg)
            logger.info(log_msg)
        elif not raw_data:
            log_msg = f"[{AgentRole.RESEARCHER}] ⚠️ 未配置 TAVILY_API_KEY，跳过新闻搜索"
            logs.append(log_msg)
            logger.warning(log_msg)
    except RECOVERABLE_ERRORS as e:
        log_msg = f"[{AgentRole.RESEARCHER}] ⚠️ 新闻搜索失败：{str(e)[:60]}"
        logs.append(log_msg)
        logger.warning(log_msg)

    if not raw_data.strip():
        return {
            **state,
            "log_messages": logs,
            "error_message": "无法获取目标公司信息，请检查 URL 是否正确或网络是否可用",
        }

    log_msg = f"[{AgentRole.RESEARCHER}] ✅ 情报收集完成，移交数据处理器"
    logs.append(log_msg)
    logger.info(log_msg)
    return {
        **state,
        "company_raw_data": raw_data,
        "log_messages": logs,
        "error_message": None,
    }
