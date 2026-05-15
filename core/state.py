from typing import TypedDict, Optional


class AgentState(TypedDict):
    # 用户输入
    product_desc: str
    icp_definition: str
    target_url: str
    language: str

    # Agent 产出
    company_raw_data: str
    company_profile: dict
    lead_score: int
    score_rationale: str
    key_hooks: list
    email_draft: dict
    market_analysis: dict

    # 流程控制
    mode: str
    log_messages: list
    error_message: Optional[str]
    should_proceed: bool
