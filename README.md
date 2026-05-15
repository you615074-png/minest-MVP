# 🤖 B2B AI SDR 数字团队

> 无人值守的 B2B 销售线索开发引擎 — 将背调+写信时间归零，让人类只专注成单。

---

## 🎯 项目简介

本系统是一个基于 LangGraph 多智能体架构的 B2B 智能销售开发平台。支持两种工作模式：

### 模式 A：SDR 精准开发（填写目标网址）

输入产品卖点 + 目标公司网址，AI 团队自动完成：

1. **🕵️ 情报挖掘** — 抓取官网 + 搜索新闻融资动态
2. **⚙️ 结构化处理** — 提取公司档案 JSON（名称、行业、规模、痛点等）
3. **📊 商机评分** — 对比 ICP 打出 0-100 分，低于 60 分自动终止
4. **✍️ 邮件生成** — 撰写引用真实钩子的个性化中文开发信

### 模式 B：市场分析（不填网址）

仅输入产品卖点，AI 自动推演目标受众画像，并推荐 5 家潜在标杆客户及其官网。

---

## 🏗️ 系统架构

```
用户输入 (Streamlit UI)
    ↓
中枢调度器 (LangGraph StateGraph · 条件路由)
    ├──[有URL]──→ 🕵️ 情报官 → ⚙️ 处理器 → 📊 打分员 ──[>60分]──→ ✍️ 文案专家
    │                                           └──[≤60分]──→ 终止
    └──[无URL]──→ 🧠 市场分析专家 → 受众画像 + 5家推荐客户
    ↓
结果展示 + 历史回溯 + 人工审核
```

**多模型分工**（通过 `.env` 自由配置）：

| Agent | 推荐模型 | 角色 | Temperature |
|---|---|---|---|
| 🧠 市场分析专家 | DeepSeek | 受众推演与客户推荐 | 0.0 |
| ⚙️ 数据处理器 | Kimi 128k | 超长文本结构化提取 | 0.0 |
| 📊 商机打分员 | DeepSeek | 逻辑推理评分 | 0.0 |
| ✍️ 文案专家 | MiniMax | 创意销售文案 | 0.2 |

---

## ⚡ 快速开始

### 1. 克隆 & 安装依赖

```bash
cd "minest MVP"
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

### 2. 配置 API Keys

```bash
copy .env.example .env
# 用编辑器打开 .env，填入你的 API Keys
```

### 3. 启动应用

```bash
# 普通启动
.venv\Scripts\streamlit.exe run app.py

# 安全模式启动（HTTPS 加密，需要 OpenSSL）
start_secure.bat
```

### 4. 注册账号

首次使用需要注册：点击右上角 **🔑 登录 / 注册** → 切换到"注册"标签 → 创建账号即可。

> 💡 **账号与数据存储说明**：
> 所有账号信息（含加密后的密码）及你的个人历史分析记录，均保存在项目根目录的本地数据库文件 **`app_data.db`** 中。
> 该文件受 `.gitignore` 保护，不会被上传至云端代码库。如需备份数据或迁移服务，仅需拷贝此文件即可。

---

## 📖 详细使用指南

### 🌐 多语言设定
在左侧配置台上方，你可以自由选择**输出语言**（支持简体中文、English、日本語等）。
即使你输入的“产品卖点”是中文，系统也会指令 AI 翻译并输出地道的目标语言报告与开发信，非常适合**出海业务**！

### 📌 模式 1：单条精准开发 (SDR 模式)
1. 切换到 **“单条开发”** 标签页。
2. 填写 **我方产品卖点**、**ICP 画像**，并输入具体的 **目标公司网址**。
3. 点击一键生成，AI 会进行全网搜索、商机打分并直接生成一封带挂钩的开发信。

### 🎯 模式 2：市场宏观分析 (Market Analysis)
1. 同样在 **“单条开发”** 标签页。
2. 填写 **我方产品卖点**，但 **留空目标网址**。
3. 点击一键分析，AI 会推演最有可能购买该产品的 1-2 类受众画像，并为你**精准推荐 5 家潜在客户公司**及其官网。

### 🗂️ 模式 3：批量导入处理 (Batch Processing)
1. 切换到 **“批量处理”** 标签页。
2. 准备一份 `CSV` 或 `Excel` 文件，确保其中包含一列名为 **`url`** 或 **`网址`**。
3. 上传文件并点击开始，系统将自动遍历处理文件中的线索。（为防触发大模型接口限流，两次查询间内置了 3 秒的防并发延迟机制）

### 📥 成果一键导出
任务运行完毕后，在右侧结果区的最下方，点击 **“📥 导出分析报告”**，即可将本次分析的结构化结果及开发信草稿打包下载为标准的 `.md` (Markdown) 文件，方便直接归档或发送给 CRM。

---

## 🔑 环境变量说明

复制 `.env.example` 为 `.env` 后填写：

```env
# === DeepSeek ===
DEEPSEEK_API_KEY=        # 在 platform.deepseek.com 获取
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=          # 例: deepseek-reasoner

# === MiniMax ===
MINIMAX_API_KEY=         # 在 api.minimax.chat 获取
MINIMAX_BASE_URL=https://api.minimax.chat/v1
MINIMAX_MODEL=           # 例: abab6.5s-chat

# === Kimi (月之暗面) ===
KIMI_API_KEY=            # 在 platform.moonshot.cn 获取
KIMI_BASE_URL=https://api.moonshot.cn/v1
KIMI_MODEL=              # 例: moonshot-v1-128k

# === 搜索工具 ===
TAVILY_API_KEY=          # 在 app.tavily.com 获取（免费1000次/月）
JINA_API_KEY=            # 可选，jina.ai 获取（不填也能用）

# === Agent 分工配置（填写 deepseek / minimax / kimi）===
ANALYZER_PROVIDER=deepseek
PROCESSOR_PROVIDER=kimi
SCORER_PROVIDER=deepseek
COPYWRITER_PROVIDER=minimax

# === 安全配置 ===
PASSWORD_SALT=           # 密码加密盐值，请填写一段随机字符串
```

> ⚠️ **安全提示**：`.env` 文件包含敏感密钥，已被 `.gitignore` 保护，**切勿提交到 Git 仓库**。

---

## 📁 项目结构

```
minest MVP/
├── app.py                    # Streamlit 主界面（含登录、双栏布局、流式执行）
├── requirements.txt          # Python 依赖
├── start_secure.bat          # HTTPS 安全启动脚本
├── .env                      # API Keys（⚠️ 不提交 Git）
├── .env.example              # Keys 模板（不含真实密钥）
├── .gitignore                # 敏感文件保护规则
│
├── core/
│   ├── state.py              # LangGraph 共享状态定义
│   ├── graph.py              # 图构建与条件路由（SDR / 市场分析双轨）
│   └── agents/
│       ├── researcher.py     # 🕵️ 情报挖掘官（Jina + Tavily）
│       ├── processor.py      # ⚙️ 数据处理器（Pydantic 结构化输出）
│       ├── scorer.py         # 📊 商机打分员
│       ├── copywriter.py     # ✍️ 破冰文案专家
│       └── market_analyzer.py# 🧠 市场分析专家（受众推演 + 客户推荐）
│
├── utils/
│   ├── helpers.py            # LLM 客户端工厂（多模型分发 + 温度控制）
│   ├── db.py                 # SQLite 数据库管理（用户表 + 历史记录表）
│   └── auth.py               # 用户认证模块（注册 / 登录 / 防暴力破解）
│
├── static/
│   └── robots.txt            # 搜索引擎爬虫拦截
│
└── .streamlit/
    └── config.toml           # 框架安全配置（CORS / XSRF / 静态托管）
```

---

## 🔒 安全特性

| 防御项 | 实现方式 |
|---|---|
| 防暴力破解 | 连续 5 次密码错误 → 账户锁定 15 分钟 |
| 密码加密 | SHA-256 加盐哈希，盐值通过环境变量管理 |
| 数据隔离 | 不同用户的历史记录通过 `user_id` 外键严格隔离 |
| 前端脱敏 | 异常信息过滤 API Key 碎片，截断长堆栈 |
| 反爬虫 | `robots.txt` 全站 Disallow |
| 跨域防护 | 关闭 CORS + 开启 XSRF 保护 |
| HTTPS 支持 | `start_secure.bat` 自动签发证书并加密启动 |

---

## 💰 费用参考

| 提供商 | 单次全流程 | Demo 10次 |
|---|---|---|
| DeepSeek | ~¥0.05 | ~¥0.5 |
| MiniMax | ~¥0.06 | ~¥0.6 |
| Kimi | ~¥0.10 | ~¥1.0 |
| Tavily | 2 credits | 20 credits（免费额度内） |

---

## 🧩 核心功能一览

- ✅ **智能双轨工作流**：填写网址即走 SDR 精准单点突破，留空网址即触发市场受众推演与客户推荐。
- ✅ **🗂️ 批量处理 (CSV/Excel)**：支持上传名单一键批量分析，内置防限流（Rate Limit）安全延迟机制。
- ✅ **🌐 国际化多语言引擎**：一键切换输出语言，中文输入，外语输出，完美赋能出海销售团队。
- ✅ **📥 成果一键导出**：分析结果与邮件草稿支持一键下载为 Markdown 文档。
- ✅ **多用户隔离系统**：原生支持多账户注册登录，各用户的历史数据通过 `app_data.db` 严格硬隔离。
- ✅ **左边栏历史回溯**：侧边栏直出历史记录清单，点击即秒开过往详情。
- ✅ **双栏独立滚动视图**：左侧输入区与右侧结果区彻底解耦，互不滚动干扰，告别传统单页瀑布流的痛点。
- ✅ **流式实时终端反馈**：AI Agent 每一步执行细节实时刷新，拒绝死板的黑屏等待。
- ✅ **金融级安全加固**：内建防暴力破解锁定机制、密码 SHA-256 加盐防脱库、前端脱敏防泄漏，并附带基于 OpenSSL 的自签名 HTTPS 启动脚本。
