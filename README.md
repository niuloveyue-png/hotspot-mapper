# Hotspot Mapper: Overseas Hot Trends → Crypto Mapping (CN-friendly)
抓取海外热点（Google Trends / Reddit / Twitter〔X, 无需官方API〕），
然后在 DexScreener 上搜索是否出现相关新币/热词，生成「套利机会清单」。

> 设计目标：帮助你尽量突破信息茧房，第一时间把**国外热点**与**币圈映射**连起来。

## 功能一览
- **Google Trends**：按国家抓取「热搜上升」关键词（pytrends）
- **Reddit**：/r/cryptocurrency, /r/memeeconomy, /r/trending 等子板块（PRAW，需要 Reddit 应用）
- **X/Twitter**：使用 `snscrape` 无需 API Key 的抓取（关键词 + 英文过滤）
- **DexScreener 映射**：用热点关键词在 DexScreener 公共检索接口中查询是否有相关代币/交易对
- **评分与筛选**：按热度、时间、新增性、是否多源共振等打分
- **导出**：输出到 `outputs/hotspots.csv` 与 `outputs/report.md`

> 可选扩展：Tokboard（TikTok 热榜）、Birdeye、CoinGecko 新增币、Pump.fun 等，你可在 `config.yaml` 启用或添加。

## 快速开始
1) **Python 环境**
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2) **配置环境变量与参数**
- 复制 `.env.example` 为 `.env`，填入你的 Reddit 凭据（只用于 Reddit 抓取）
- 编辑 `config.yaml` 调整地区、关键词、阈值等

3) **运行**
```bash
python -m src.main
```
首跑会在 `outputs/` 生成 CSV 和 Markdown 报告。

4) **定时运行（CRON 或 GitHub Actions）**
- 本地 Linux/Mac 可用 `crontab -e`：
  ```
  0 9 * * * cd /path/to/hotspot-mapper && . .venv/bin/activate && python -m src.main >> run.log 2>&1
  ```
- GitHub Actions：见 `.github/workflows/schedule.yml`，fork 后把 secrets 配置好（可选）。

## 重要说明
- **网络访问**：本项目需要能访问海外站点；建议在“纯英文环境”的代理节点下运行（系统语言/时区可设为 en-US / 美国时区）。
- **合法合规**：仅用于公开数据的趋势研究，不构成投资建议。交易有风险，谨慎评估。

## 目录结构
```
hotspot-mapper/
  ├─ src/
  │  ├─ sources/
  │  │  ├─ google_trends.py
  │  │  ├─ reddit.py
  │  │  └─ twitter.py
  │  ├─ mapping/
  │  │  └─ dexscreener.py
  │  ├─ scoring.py
  │  ├─ export.py
  │  └─ main.py
  ├─ config.yaml
  ├─ requirements.txt
  ├─ .env.example
  └─ .github/workflows/schedule.yml
```

## 常见问题
- **为什么没有 TikTok/Tokboard 直接抓取？** 官方 API 限制较多、稳定性差。建议先跑核心模块（Trends/Reddit/Twitter），后续可在 `sources/` 中扩展抓取器。
- **Twitter/X 抓不到？** `snscrape` 依赖网页可访问性与反爬策略，建议固定海外 IP，必要时降低抓取频率。
- **DexScreener 搜索结果很多？** 使用 `config.yaml` 的关键词白/黑名单与最小流动性阈值进行过滤；并结合“发行时间/新近度”做筛选。


## 飞书群推送（可选）
1. 在飞书群里添加 **自定义机器人** → 复制 **Webhook**。
2. 打开 `config.yaml`，在 `notify.feishu.webhook` 填入 Webhook（或在运行环境设置成环境变量并在代码里读取）。
3. 如开启了“签名校验”，在运行环境里设置：`FEISHU_BOT_SECRET="你的签名密钥"`。
4. 运行脚本后，会自动把**热点 Top**与**DexScreener 映射 Top**以**交互卡片**的形式推送到群里。


## Telegram 推送（可选）
1. 在 @BotFather 创建一个 Bot，拿到 *BOT_TOKEN*（例如 `123456:ABC-DEF...`）。
2. 获取你的 *chat_id*：给你的 Bot 发一条消息，然后访问  
   `https://api.telegram.org/bot<BOT_TOKEN>/getUpdates` 在返回中找到 `chat.id`（或把 Bot 拉进群，使用群的 chat_id）。
3. 配置：
   - 将环境变量 `TELEGRAM_BOT_TOKEN` 设置为你的 token（也可直接在 `config.yaml` 写死 `token_env` 指向的变量）。
   - 在 `config.yaml` → `notify.telegram.chat_id` 填入 chat_id，`enabled: true`。
4. 运行后，会发送 Markdown 卡片（自动分段，处理 4096 限制；包含 Hotspots / Dex 映射 / Pump.fun）。
> 受网络环境影响，建议在海外服务器或可直连 Telegram 的代理环境运行；如在大陆运行，需自行准备网络出口（合规前提下）。
