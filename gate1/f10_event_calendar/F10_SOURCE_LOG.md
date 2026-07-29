# F10 官方事件日历 — 来源与证据日志

```yaml
task_id: M4-T1 / SA-1
role: 证据采集与结构化提取（evidence-first）
frozen_ref: STUDY_0_PREREGISTRATION.md 行 62 — is_event_day ∈ {CPI, NFP, FOMC, none}（BLS/Fed 官方时刻表快照）
window: 2010-06-06 → 2021-12-31（含端点）
timezone: America/New_York（所有 date_et 为 ET 日历日）
evidence_tier: Level 1（实际官方文件 + checksum），全部来源在硬白名单内
status: 表已产出并通过全部测试；两项决策待 Aaron 批复（见 §8）
real_s0_not_run: true
frozen_files_untouched: true
```

## 0. 摘要

| 项 | 值 |
|---|---|
| 事件行数 | 468 |
| CPI 行 | 139 |
| NFP 行 | 138 |
| FOMC 行（会议日 + statement 日） | 191 |
| 其中 is_fomc_statement_day = true | 96 |
| 原始件总数 | 140（BLS 15 + Fed 索引/支撑 14 + FOMC statement 页 111） |
| 官方来源域名 | `www.bls.gov`、`www.federalreserve.gov` |
| 缺失年份 | **无**（2010–2021 每一年都有 Level 1 官方来源） |
| 官方来源相互冲突 | **无**（交叉互证 100% 一致，见 §4） |
| 未达 Level 1 的字段 | FOMC `official_release_time_et` 在 2010–2015 共 45 行（见 §5.5，已开 DECISION_PACKET，**未凭记忆填写**） |

## 1. 抓取方法与可复现性

**域名白名单（硬性）**：仅 `*.bls.gov` 与 `*.federalreserve.gov`。没有任何第三方
经济日历、经纪商日历、新闻、博客、搜索摘要或模型记忆进入事件表。注册表 fragment
中每条 URL 的主机名由 `tests/test_f10_calendar.py::test_all_sources_are_on_the_official_whitelist`
强制校验。

**federalreserve.gov**：允许常规 HTTP 客户端直连，用 `requests` 抓取，
落盘原始字节并即时计算 SHA-256。

**bls.gov**：对非浏览器客户端一律返回 **HTTP 403**（已用 `Invoke-WebRequest`、
`curl`、`requests` 三种客户端在多组 User-Agent 下复验，均为 403；`data.bls.gov`
与 `download.bls.gov` 同样 403）。因此改用内置浏览器会话抓取——与本项目
`gate1/G9_EVIDENCE_RESOLUTION.md` 中 CME 费表的取证范式一致：

1. 浏览器在 `https://www.bls.gov` 源内 `fetch()` 目标页，取 `ArrayBuffer`；
2. 浏览器端用 `crypto.subtle.digest('SHA-256', ...)` 计算摘要；
3. 原始字节 POST 到本机 loopback sink（`127.0.0.1`），由 sink 逐字节写盘；
4. 落盘后由 Python 重新计算 SHA-256，与浏览器端摘要**逐一比对**。

15 个 BLS 原始件的两侧摘要**全部一致**（`sha_match_browser: true`），
记录在 `raw/_fetch_manifest_bls.json`。这排除了传输截断或转码。

**抓取时间**：2026-07-29 UTC（逐文件精确时间见 §2 表格与注册表 fragment）。

**提取的确定性**：`f10_extraction.py` 只读 `raw/`，不联网，重跑产生字节相同的
`f10_events.csv`（连续两次运行 `csv_sha256` 相同；测试
`test_extraction_is_deterministic_and_offline` 在 socket 被 monkeypatch 封死的
情况下重跑提取并与磁盘 CSV 做字节比对）。

```
f10_events.csv  sha256 = 3c3401f6cf7cd4933fcd47dc374fd138e441c5b6a869a48ae078816dd7afcb00
```

## 2. 来源清单（索引 / 日程 / 支撑类，29 件）

### 2.1 URL 与页面标题

| file | original URL | final URL (after redirect) | page title |
|---|---|---|---|
| `bls_archived_sched_index.htm` | https://www.bls.gov/bls/archived_sched.htm | (same) | Schedules for Selected BLS Economic News Releases for Prior Years : U.S. Bureau of Labor Statistics |
| `bls_newsrelease_archive_cpi.htm` | https://www.bls.gov/bls/news-release/cpi.htm | (same) | Consumer Price Index Archived News Releases : U.S. Bureau of Labor Statistics |
| `bls_newsrelease_archive_empsit.htm` | https://www.bls.gov/bls/news-release/empsit.htm | (same) | Employment Situation Archived News Releases : U.S. Bureau of Labor Statistics |
| `bls_schedule_2010_home.htm` | https://www.bls.gov/schedule/2010/home.htm | (same) | Schedule of Releases for 2010 |
| `bls_schedule_2011_home.htm` | https://www.bls.gov/schedule/2011/home.htm | (same) | Schedule of Releases for 2011 |
| `bls_schedule_2012_home.htm` | https://www.bls.gov/schedule/2012/home.htm | (same) | Schedule of Releases for 2012 |
| `bls_schedule_2013_home.htm` | https://www.bls.gov/schedule/2013/home.htm | (same) | Schedule of Releases for 2013 |
| `bls_schedule_2014_home.htm` | https://www.bls.gov/schedule/2014/home.htm | (same) | Schedule of Releases for 2014 |
| `bls_schedule_2015_home.htm` | https://www.bls.gov/schedule/2015/home.htm | (same) | Schedule of Releases for 2015 |
| `bls_schedule_2016_home.htm` | https://www.bls.gov/schedule/2016/home.htm | (same) | Schedule of Releases for 2016 |
| `bls_schedule_2017_home.htm` | https://www.bls.gov/schedule/2017/home.htm | (same) | Schedule of Selected Releases 2017 |
| `bls_schedule_2018_home.htm` | https://www.bls.gov/schedule/2018/home.htm | (same) | Schedule of Selected Releases 2018 |
| `bls_schedule_2019_home.htm` | https://www.bls.gov/schedule/2019/home.htm | (same) | Schedule of Selected Releases 2019 |
| `bls_schedule_2020_home.htm` | https://www.bls.gov/schedule/2020/home.htm | (same) | Schedule of Selected Releases 2020 |
| `bls_schedule_2021_home.htm` | https://www.bls.gov/schedule/2021/home.htm | (same) | Schedule of Selected Releases 2021 |
| `fed_fomccalendars.htm` | https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm | (same) | The Fed - Meeting calendars and information |
| `fed_fomchistorical2010.htm` | https://www.federalreserve.gov/monetarypolicy/fomchistorical2010.htm | (same) | The Fed - 2010 |
| `fed_fomchistorical2011.htm` | https://www.federalreserve.gov/monetarypolicy/fomchistorical2011.htm | (same) | The Fed - 2011 |
| `fed_fomchistorical2012.htm` | https://www.federalreserve.gov/monetarypolicy/fomchistorical2012.htm | (same) | The Fed - 2012 |
| `fed_fomchistorical2013.htm` | https://www.federalreserve.gov/monetarypolicy/fomchistorical2013.htm | (same) | The Fed - 2013 |
| `fed_fomchistorical2014.htm` | https://www.federalreserve.gov/monetarypolicy/fomchistorical2014.htm | (same) | The Fed - 2014 |
| `fed_fomchistorical2015.htm` | https://www.federalreserve.gov/monetarypolicy/fomchistorical2015.htm | (same) | The Fed - 2015 |
| `fed_fomchistorical2016.htm` | https://www.federalreserve.gov/monetarypolicy/fomchistorical2016.htm | (same) | The Fed - 2016 |
| `fed_fomchistorical2017.htm` | https://www.federalreserve.gov/monetarypolicy/fomchistorical2017.htm | (same) | The Fed - 2017 |
| `fed_fomchistorical2018.htm` | https://www.federalreserve.gov/monetarypolicy/fomchistorical2018.htm | (same) | The Fed - 2018 |
| `fed_fomchistorical2019.htm` | https://www.federalreserve.gov/monetarypolicy/fomchistorical2019.htm | (same) | The Fed - 2019 |
| `fed_fomchistorical2020.htm` | https://www.federalreserve.gov/monetarypolicy/fomchistorical2020.htm | (same) | The Fed - 2020 |
| `fed_ne_press_feed.json` | https://www.federalreserve.gov/json/ne-press.json | (same) | (JSON feed: Board press releases) |
| `fed_press_20110324a_press_briefings.htm` | https://www.federalreserve.gov/newsevents/pressreleases/monetary20110324a.htm | (same) | Federal Reserve Board - Chairman Bernanke will hold press briefings four times per year to present the FOMC&#39;s current economic projections and to provide additional context for policy decisions |

### 2.2 哈希、体积、抓取时间、覆盖年份

`extracted-rows SHA-256` = 该来源在 `f10_events.csv` 中所归属行的
（date_et, event_type, official_release_time_et, 三个布尔位）连接后的摘要，
用于把"原始件"与"它实际产出的表内容"绑定。

| # | file | SHA-256 (raw) | bytes | HTTP | fetched (UTC) | years | extracted-rows SHA-256 |
|---|---|---|---|---|---|---|---|
| 1 | `bls_archived_sched_index.htm` | `d37ead2c975f3a15e56ed3e663ffc8dd479dccc373fb1ad2e0ed970bda9a764f` | 48433 | 200 | 2026-07-29T02:25:23 | 2010-2021 (index) | `-` |
| 2 | `bls_newsrelease_archive_cpi.htm` | `f1380f1997e2b0b93add8739e1aea433a8e3255104ead868a4c1ec96a0420e87` | 128157 | 200 | 2026-07-29T02:25:24 | 1995-2026 (cross-check witness) | `-` |
| 3 | `bls_newsrelease_archive_empsit.htm` | `2e55df17109bbf28d47e8b154b76e010b1e815472d61650fbd0a52f099d39fe7` | 132521 | 200 | 2026-07-29T02:25:24 | 1995-2026 (cross-check witness) | `-` |
| 4 | `bls_schedule_2010_home.htm` | `d07824c812ed3676a23d4de786ce6b082296fd24a11c09bfb46fd30fb1a0fdbf` | 96888 | 200 | 2026-07-29T02:25:22 | 2010 | `18fc8834bb0a3fe414455c3b78263b34159e18f59549276ae76ff9b45139a282` |
| 5 | `bls_schedule_2011_home.htm` | `29059f51f44d18c231066c5741536c61a53c492b98815767115db0728ef1151e` | 95456 | 200 | 2026-07-29T02:25:23 | 2011 | `3838a2d768db5e6284452d7116160a15eb34cc200c889d558f5d8616109b513b` |
| 6 | `bls_schedule_2012_home.htm` | `833f2e4fa96f44d43d6d946c268df3ce3e449db297b2dede7622217556774c9a` | 97388 | 200 | 2026-07-29T02:25:23 | 2012 | `5e2ba3d2d5cfac3cc7f8e9f6906672de7deef816954863fee80c02b9a1d95feb` |
| 7 | `bls_schedule_2013_home.htm` | `d161098b85c2cb39d611b3178ece8220371f1443aebf38d8724d34a967960a44` | 93601 | 200 | 2026-07-29T02:25:23 | 2013 | `4d40ceaee08306510ecfad6b70767fbaf70452b7b9063bd84a4b5e0ea14c5651` |
| 8 | `bls_schedule_2014_home.htm` | `fadc4e1bd77b5776ffde8bfb0439621f3928e8bf2d12333ac646139cdc0665b1` | 91623 | 200 | 2026-07-29T02:25:23 | 2014 | `1e93a1b8e9f08745df6870677ebb93a49c2fc0eb3e025d4d3c28a0faa0670bfb` |
| 9 | `bls_schedule_2015_home.htm` | `49d76a674845c8d8c53ee7256fb633d50489befb8db0c588ad35c4eea18636f4` | 96776 | 200 | 2026-07-29T02:25:23 | 2015 | `f6e1a1e4e025aef75e0b9da5a8ff5202f0dad5567080044eae94d145d8d66493` |
| 10 | `bls_schedule_2016_home.htm` | `528b11ae512d19ac45dd17be7308b8f03f2158220f97eecb6f918af908b98fa9` | 96638 | 200 | 2026-07-29T02:25:23 | 2016 | `ee7a041e9d5d39ebb372a16df3d5fa6a95ba855b7bec1c7adc7287f69ff0091c` |
| 11 | `bls_schedule_2017_home.htm` | `8bf4fd6580ab000f0600478ab8a1519fad673d3d9c9ac6347aa9fbb31037fd82` | 95245 | 200 | 2026-07-29T02:25:23 | 2017 | `b009461d7e3519f3d744de138532532314d44e813400ae3be1fe1330f8c389bf` |
| 12 | `bls_schedule_2018_home.htm` | `9d807f198289be7655a45cc5725783a41c8e58446b8c484a9b862eac5c8f1ddb` | 98227 | 200 | 2026-07-29T02:25:23 | 2018 | `b2e39b686dc8c58fe5df36e224ed070e446fc251c2721692a84868b460242b6c` |
| 13 | `bls_schedule_2019_home.htm` | `8a2ffae139a8a593d70b26c980c8ffe48047e9105d94319bead2a25378a3d365` | 99234 | 200 | 2026-07-29T02:25:23 | 2019 | `40983e64431c53eeb46e766e576899cb51c2f666b574036c7056a2f9764eaa1f` |
| 14 | `bls_schedule_2020_home.htm` | `bcbb7b1fe1ae19f5d1ec74c1d8bed91e7573142f0797b690fcd6686ea9f83191` | 93728 | 200 | 2026-07-29T02:25:23 | 2020 | `b1af92389503a24850bd51507fb03dda832ff5c1eb1e09ce50a47946fa93f321` |
| 15 | `bls_schedule_2021_home.htm` | `68e293324a32bd0ec63415cfa38e5f501e73cd3896148900b08b5a091eb3c8da` | 98330 | 200 | 2026-07-29T02:25:23 | 2021 | `5abcd2edd8f01eea9cb230eb0b4ad3bcd5464b602cd31472138387cb3a60351d` |
| 16 | `fed_fomccalendars.htm` | `83258b54c39eac52daf85408252168214d0ba2f58eff0538cdaa41e2030d2d1d` | 164114 | 200 | 2026-07-29T02:20:29 | 2021 | `8fdc4d0695abeac43669c7609ffb8f15a09a1211125d5a729e8c2e28a899e9cd` |
| 17 | `fed_fomchistorical2010.htm` | `ec8346d1c2a7424a3f9f1cf9f559f80e82089ffc5289a971b2e34ffedddc03ba` | 96176 | 200 | 2026-07-29T02:20:17 | 2010 | `46037f26ce3745a66e356e9f69b9c0d104d353e32bf48bcb9ce9bb87de2a5e34` |
| 18 | `fed_fomchistorical2011.htm` | `f00210b38b30350b3cf2e0b34f7eaa1da5eeec99134a3e869bb009fa986e2d19` | 98183 | 200 | 2026-07-29T02:20:18 | 2011 | `038655070d77a222355df2d79c213e500bda925279abc9bb64766baece7e886c` |
| 19 | `fed_fomchistorical2012.htm` | `0cd5a0b0c3fb10d9d5d81df457e8ef3803ffe4817985f1b949b6f3e416649a8c` | 98104 | 200 | 2026-07-29T02:20:20 | 2012 | `1ab7b92128a4310f82054adb4cd81a4064a5ca53ebdb4d79b02e8a387d032266` |
| 20 | `fed_fomchistorical2013.htm` | `159f4af531a3c1583859908811eea98e8da8128040573403ba3bd593bec48295` | 95765 | 200 | 2026-07-29T02:20:21 | 2013 | `b0af77a0c4dda4948a4337f184a92a7937de9b70cddd8f58a2fcda49ca3472ba` |
| 21 | `fed_fomchistorical2014.htm` | `ea128b586dc130603ea3f4a2edf0c2b88e0b3766b0b137ba30fbce7bb366978d` | 96045 | 200 | 2026-07-29T02:20:22 | 2014 | `e09ffd55d2fd0e7d895e363c6fe59cea5a4ee94b4fb64cdc80b02cb6593aeaa9` |
| 22 | `fed_fomchistorical2015.htm` | `6abdeaad2e30203bf17e3aff5d4a7a1b24f91f22c24589d7ae06941ed1aedce5` | 95197 | 200 | 2026-07-29T02:20:23 | 2015 | `fa6a9ee929a4c35e09394b6b075c54a5b0ebb9426f40d45ea9215c3947ed7b00` |
| 23 | `fed_fomchistorical2016.htm` | `2b530c178d143dd743a9d60ff3fad4ef113ac67e401f84402ce2f43c4a67fd94` | 95785 | 200 | 2026-07-29T02:20:24 | 2016 | `f6c541cd4a5ad9039fe34ea8474369f37e60885cd2d667886a18a24a36b9f216` |
| 24 | `fed_fomchistorical2017.htm` | `5727064f5cdc3c00b34a6dd557578e8536c0cd4704b0fc428c0a046337f5dfed` | 95156 | 200 | 2026-07-29T02:20:25 | 2017 | `f9617b15ad7b2fd0f080a4cb9835eb7f89e131837f3ceaafd5243cfd251e2692` |
| 25 | `fed_fomchistorical2018.htm` | `bf7e5388664898ba19f3c7be94126e0741b205a7ca485ae36cb0810189658a16` | 95661 | 200 | 2026-07-29T02:20:26 | 2018 | `d9b76390a7166afed60bcbe5230149f184e7c7f48243429ca261782b6fd4b65e` |
| 26 | `fed_fomchistorical2019.htm` | `01d922d94d021b6dfe7c9ceb403fbc434cdd88b734dbd104476f90b066c8b08b` | 97300 | 200 | 2026-07-29T02:20:27 | 2019 | `91d6e8364d79ee4d4f51e6db422045278e3b02207aefdf103fb6c6beef5c2666` |
| 27 | `fed_fomchistorical2020.htm` | `9cd0affb51ab6ab91a03a9a27f30d4f195e758f9c7d56c8dce40ec00ed0ef3e7` | 98511 | 200 | 2026-07-29T02:20:28 | 2020 | `623c8fbb0f39543700491150d93cf2139964024fbfa41ca29f9b6b824c42b507` |
| 28 | `fed_ne_press_feed.json` | `9820949c4769be489661df4356249d513ec4d74edf88af7bcb072fb6ce6ab452` | 991315 | 200 | 2026-07-29T02:37:17 | 2006-2026 (supporting) | `-` |
| 29 | `fed_press_20110324a_press_briefings.htm` | `a391ba3cba12f0712303315f94fbdbb4ef1fbfdd4b10191cf4fbb80ad103589c` | 81713 | 200 | 2026-07-29T02:37:16 | 2011 (supporting) | `-` |

## 3. 各来源承担的角色

| 角色 | 来源 | 说明 |
|---|---|---|
| CPI / NFP 日期与官方时刻（主） | `bls_schedule_<year>_home.htm` | BLS 年度发布日程存档页，逐条给出 Date / Time / Release。**发布名以 `<strong>` 精确匹配**，因此 "Employment Situation of Veterans"（年度、无关）不会被误当成月度 "Employment Situation" |
| CPI / NFP 日期（互证） | `bls_newsrelease_archive_cpi.htm`、`bls_newsrelease_archive_empsit.htm` | BLS 新闻稿存档页，链接文件名内嵌**实际发布日**（`cpi_MMDDYYYY.htm`），是与日程页相互独立的第二证人 |
| 年度日程页可达性索引 | `bls_archived_sched_index.htm` | 官方"往年日程"索引，证明 2010–2021 全部 12 年均由 BLS 官方提供 |
| FOMC 会议日（2010–2020） | `fed_fomchistorical<year>.htm` | FOMC 历史材料页，逐次会议给出标题（含 Conference Call / unscheduled / notation vote / cancelled 标注）与 Statement 链接 |
| FOMC 会议日（2021） | `fed_fomccalendars.htm` | FOMC 日历页（覆盖 2021–2027）；2021 尚未进入"历史材料"发布周期 |
| FOMC statement 发布日与时刻（主） | `fed_statement_<yyyymmdd><s>.htm` | 逐份 statement 新闻稿页；`article__time` 给发布日，`releaseTime` 在 2016 年起给出 "For release at H:MM p.m. E[SD]T" |
| 支撑材料（不进表） | `fed_press_20110324a_press_briefings.htm`、`fed_ne_press_feed.json` | 仅用于 §5.5 的时刻问题论证，见 DECISION_PACKET；**未用于填任何字段** |

## 4. 交叉互证结果

### 4.1 BLS：年度日程页 ↔ 新闻稿存档页

| 事件 | 日程页日期数（2010–2021） | 存档页日期数（2010–2021） | 差集 |
|---|---|---|---|
| CPI | 144 | 144 | 空 |
| Employment Situation (NFP) | 144 | 144 | 空 |

两个独立官方证人在 12 年、288 个发布日上**逐日完全一致**，无一处冲突。
该断言在 `f10_extraction.py` 内是硬断言（不一致即抛 `SourceConflict`，
等同 STOP），并由 `test_bls_witnesses_agree` 复核。

### 4.2 Federal Reserve：日历/历史页 ↔ 逐份 statement 页

对每一条 Statement 链接，提取脚本比对**链接文件名内嵌日期**与
**statement 页 `article__time` 正文日期**；不一致即抛 `SourceConflict`。
96 份 statement 全部一致。

## 5. 异常、偏差与显式说明

### 5.1 2010 为不完整年（窗口起点）

冻结开发窗口自 **2010-06-06** 开启，故 2010 年只计入该日之后的事件：
CPI 7 次（首条 2010-06-17）、NFP 6 次（首条 2010-07-02）、
FOMC statement 5 次。这不是数据缺失。

同理，2021 年末最后一个事件为 **2021-12-15**（FOMC statement）；
2021-12-16 至 2021-12-31 无本表所辖事件。

### 5.2 2013 年联邦政府停摆导致的延期发布（对应决策 D3）

BLS 年度日程存档页记录的是**实际发布日**（已反映停摆后的改期），与新闻稿
存档页内嵌的实际发布日一致：

| 事件 | 参考月 | 实际发布日（本表采用） | 官方出处 |
|---|---|---|---|
| Employment Situation | 2013 年 9 月 | **2013-10-22**（周二，08:30 ET） | `bls_schedule_2013_home.htm` + `bls_newsrelease_archive_empsit.htm`（`empsit_10222013.htm`） |
| Consumer Price Index | 2013 年 9 月 | **2013-10-30**（周三，08:30 ET） | `bls_schedule_2013_home.htm` + `bls_newsrelease_archive_cpi.htm`（`cpi_10302013.htm`） |

2013 年 CPI 与 NFP 各仍为 12 次（无发布被取消，只被推迟）。
**如何编码延期发布属 D3，SA-1 不做决定**，只如实记录官方实际发布日期。

### 5.3 FOMC：非标准日历条目分类表（对应决策 D2 的延伸）

官方页面把 FOMC 条目区分为 Meeting / Conference Call / (unscheduled) /
(notation vote) / (cancelled)。本表**如实收录所有实际发生的条目**，
不自行筛选；筛选规则属 D2，由 Aaron + main agent 决定。完整非标准条目如下：

| 官方标题 | 类别 | 会议日 | 对应 statement 日 | 是否在窗口内 |
|---|---|---|---|---|
| May 9 Conference Call - 2010 | Conference Call | 2010-05-09 | 2010-05-09（21:15 ET，周日，与 ECB/BoE 等联合声明） | 否（早于 2010-06-06） |
| October 15 Conference Call - 2010 | Conference Call | 2010-10-15 | 无 | 是 |
| August 1 Conference Call - 2011 | Conference Call | 2011-08-01 | 无 | 是 |
| November 28 Conference Call - 2011 | Conference Call | 2011-11-28 | 无 | 是 |
| October 16 (unscheduled) - 2013 | unscheduled | 2013-10-16 | 无 | 是 |
| March 4 (unscheduled) - 2014 | unscheduled | 2014-03-04 | 无 | 是 |
| October 4 (unscheduled) - 2019 | unscheduled | 2019-10-04 | **2019-10-11**（11:00 ET） | 是 |
| March 2 (unscheduled) Meeting - 2020 | unscheduled | 2020-03-02 | **2020-03-03**（10:00 ET） | 是 |
| March 15 (unscheduled) Meeting - 2020 | unscheduled | 2020-03-15 | **2020-03-15**（17:00 ET，周日） | 是 |
| March 17-18 (cancelled) Meeting - 2020 | **cancelled** | — | 无 | **已排除，见 5.4** |
| March 19 (notation vote) - 2020 | notation vote | 2020-03-19 | 无 | 是 |
| March 23 (notation vote) - 2020 | notation vote | 2020-03-23 | **2020-03-23**（08:00 ET） | 是 |
| March 31 (notation vote) - 2020 | notation vote | 2020-03-31 | 无 | 是 |
| August 27 (notation vote) - 2020 | notation vote | 2020-08-27 | 无 | 是 |

注：2019-10-04 的 unscheduled 会议，其 statement 于 **2019-10-11** 才发布
（相隔 7 天）——这是"会议日 ≠ statement 日"最极端的一例，schema 的
`is_fomc_statement_day` 正为此设计。

### 5.4 唯一一处主动排除：2020-03-17/18（cancelled）

官方标题写明 `March 17-18 (cancelled) Meeting - 2020`：该次例会**未召开**
（已被 2020-03-15 的临时会议取代）。把它记为事件日等于断言一个未发生的事实，
故 **2020-03-17 与 2020-03-18 不进入 `f10_events.csv`**。
该排除由 `test_cancelled_meeting_is_absent` 锁定。除此之外没有任何条目被
SA-1 主动过滤。

### 5.5 FOMC `official_release_time_et` 的证据缺口（2010–2015，45 行）

- 2016 年起，statement 新闻稿页正文含 `For release at H:MM p.m. E[SD]T`，
  可直接作为 Level 1 时刻证据（本表 51 行由此填入）。
- 2010–2015 的 statement 页（现行归档版本）一律只写
  **"For immediate release"**，不含时钟时间；对应的 PDF 直链
  （`/monetarypolicy/files/monetary<yyyymmdd>a1.pdf`）在这些年份返回 404。
- 因此这 45 行的 `official_release_time_et` 填入哨兵值
  **`NOT_ATTESTED_IN_OFFICIAL_SOURCE`**，**没有凭记忆或第三方来源补齐**。

已排除的两个候选替代源（两者都已归档，供 Aaron 判断）：

1. `fed_press_20110324a_press_briefings.htm`（2011-03-24 官方新闻稿）写明
   2011 年 4/27、6/22、11/2 三次会议 "the FOMC statement **is expected to be
   released at around 12:30 p.m.**, one hour and forty-five minutes earlier
   than for other FOMC meetings"。这是**事前预告**（"expected"、"around"），
   不是对实际发布时刻的官方记录，故未用于填表。
2. `fed_ne_press_feed.json`（理事会新闻稿 JSON feed）对每条新闻稿带时间戳，
   但该时间戳是**上站时间**而非官方发布时刻——例如 2010 年各次 statement
   一律为 `2:20:00 PM`、2011-04-27 为 `12:40:00 PM`，系统性晚于既定发布时刻
   数分钟。故不可作为 `official_release_time_et`。

→ 见 `DECISION_PACKET_F10_D4A_FOMC_RELEASE_TIME.md`。
**注意：该缺口只影响时刻列，不影响任何事件日期**；F10 冻结定义
（`is_event_day` 为日级类别）不依赖时刻列。

### 5.6 逐年计数表（含全部偏差）

基线：CPI 每年 12、NFP 每年 12、FOMC statement 每年 8。

| 年 | CPI | NFP | FOMC 会议日 | FOMC statement | 偏差说明与官方出处 |
|---|---|---|---|---|---|
| 2010 | 7 | 6 | 8 | 5 | 窗口自 06-06 开启（§5.1），非缺失 |
| 2011 | 12 | 12 | 15 | 8 | 会议日含 2 次 conference call（08-01、11-28），均无 statement |
| 2012 | 12 | 12 | 15 | 8 | 基线 |
| 2013 | 12 | 12 | 17 | 8 | 含 10-16 unscheduled；停摆改期见 §5.2 |
| 2014 | 12 | 12 | 17 | 8 | 含 03-04 unscheduled |
| 2015 | 12 | 12 | 16 | 8 | 基线 |
| 2016 | 12 | 12 | 16 | 8 | 基线 |
| 2017 | 12 | 12 | 16 | 8 | 基线 |
| 2018 | 12 | 12 | 16 | 8 | 基线 |
| 2019 | 12 | 12 | 18 | **9** | 10-04 unscheduled，其 statement 于 **2019-10-11** 发布 |
| 2020 | 12 | 12 | 21 | **10** | 7 次例会（03-17/18 **取消**）+ 03-03、03-15、03-23 三次临时/notation 声明 |
| 2021 | 12 | 12 | 16 | 8 | 基线；来源为 `fed_fomccalendars.htm` |

"FOMC 会议日"计每一个日历日（两日例会计 2 行），故常见值为 16。

### 5.7 同日多事件

窗口内共 **19** 天同时承载两类事件（18 天 CPI+FOMC、1 天 NFP+FOMC：
2019-10-04）。按冻结要求**每事件独立一行、不合并、不定优先级**；
合并/优先级规则属 **D1**，SA-1 未做任何编码。

## 6. 缺失与不可达

**无。** 2010–2021 全部 12 年、三类事件均有 Level 1 官方来源，
HTTP 状态全部 200。没有任何年份用低级来源顶替。

唯一的证据不足是 §5.5 的时刻列（字段级，非年份级），已用哨兵值显式标注
并上交决策，未静默降级。

## 7. FOMC statement 原始件清单（111 件）

说明：这 111 件是从 FOMC 历史页/日历页中出现的 `monetary<yyyymmdd>[a-z].htm`
链接**全量**抓取的（超集），其中被 `f10_events.csv` 实际引用的为 96 件；
其余为同页出现的实施说明（implementation note）等，归档但不进表。

| # | file | SHA-256 (raw) | bytes | HTTP | fetched (UTC) | years | extracted-rows SHA-256 |
|---|---|---|---|---|---|---|---|
| 1 | `fed_statement_20100127a.htm` | `f9dc5a8c8d211b95a7911c98ab1fe4ee10f4de59b0772764f8d10991b0cfffb3` | 82929 | 200 | 2026-07-29T02:20:37 | 2010 | `-` |
| 2 | `fed_statement_20100316a.htm` | `1f96c207b639dd7a12bf11618d6364591640b4f3e0c551678eea127fb39d5a9f` | 82388 | 200 | 2026-07-29T02:20:38 | 2010 | `-` |
| 3 | `fed_statement_20100428a.htm` | `73db080e1dff5ec2695c1c028830f30921086aa73281b93fa501cc71627cf766` | 82130 | 200 | 2026-07-29T02:20:40 | 2010 | `-` |
| 4 | `fed_statement_20100509a.htm` | `63f35a8ca8a40c48c4246076266e35c5bf494677a7e6c35ff7ab49b648a35978` | 83374 | 200 | 2026-07-29T02:20:41 | 2010 | `-` |
| 5 | `fed_statement_20100623a.htm` | `48f45a4187a7339029dd4429ce84d5fd4653851882a87d1717030c248a27a8a7` | 81850 | 200 | 2026-07-29T02:20:43 | 2010 | `c3364e0685c6951ad0d05ccbf8707ae8a038bf3c3e38f13cf03f481be83eee0d` |
| 6 | `fed_statement_20100810a.htm` | `8071b1ea4b20ca36f866b7584ccce1ecdc967990ab3bab8fb563d0af893dc7e9` | 82844 | 200 | 2026-07-29T02:20:44 | 2010 | `7636f0eb89124a6bea45c0a49c714008e43ad63fe6348bb18afb3e94c28bfcdf` |
| 7 | `fed_statement_20100921a.htm` | `c2f8e6363a91c80e4416b671f0fc54304f63c4387a44b6a8a6985dd9d0339305` | 82302 | 200 | 2026-07-29T02:20:46 | 2010 | `c668bbbaa2cf9b15b7e4791a89b46d74dcf5acf3f9f3aa46ea221dc50cea69c0` |
| 8 | `fed_statement_20101103a.htm` | `e772995f1e601a03338f396a1728545fb412fc8ab96587187d36f433a7255148` | 82891 | 200 | 2026-07-29T02:20:47 | 2010 | `4d9c8e48c4388d77cc64c754321435f51e608a4248ef3d163c31d5e7f457c9b5` |
| 9 | `fed_statement_20101214a.htm` | `a63c144c9ea708727ed5ee0d1bd20df6b4e6b9278983be12901a0373d42327d1` | 82740 | 200 | 2026-07-29T02:20:48 | 2010 | `12b6e4a5d8d646847f3522b9a6dab422d609384a539c89175c6b8733a54816ed` |
| 10 | `fed_statement_20110126a.htm` | `5bcba7edf47ebe30b7d258379bdcc01fda03d2876611856fc66d953dfcc88522` | 82373 | 200 | 2026-07-29T02:20:49 | 2011 | `376b14fc2c193a4aff485bca63945f1b65de4bbd9b186cc9dfd42dde9387a08d` |
| 11 | `fed_statement_20110315a.htm` | `de853f9e15ab9c06fa6f77423f541cc100ae6a9821187b8626060af79516186c` | 82515 | 200 | 2026-07-29T02:20:51 | 2011 | `df6d3d111854d596fc2c99f4c0441adb0869af502a6101dfd754df60aa4d0df9` |
| 12 | `fed_statement_20110427a.htm` | `1c27d183491cdea4587478bd0878fd20d69ec5545732f1ec2ea060b5d48106cc` | 82580 | 200 | 2026-07-29T02:20:52 | 2011 | `77123d8207bd80922d68da2ab1e6c003167ce174788e532015c4fe29527ff397` |
| 13 | `fed_statement_20110622a.htm` | `539a35f2192bb2588ce714958392cb7ff6e66b41b3f79b6401a5809416907276` | 82525 | 200 | 2026-07-29T02:20:53 | 2011 | `d693a827699be6332e705684da01864c15cad6056cfde5bbcb4eb506dd66bcd0` |
| 14 | `fed_statement_20110809a.htm` | `c0ab6461fab043db4765edc989827a1e69dec47ecdcf2d3fa6cbe54027b2ff07` | 82998 | 200 | 2026-07-29T02:20:54 | 2011 | `7194b7e706b7ad11fe13c8b0d2713b93c9ea96ead62deb584e635bce9ea477bb` |
| 15 | `fed_statement_20110921a.htm` | `89e9ed94f16aecc1da328bc8fe8a56d4c1089f48019365d341878cd25c64e6e6` | 84231 | 200 | 2026-07-29T02:20:55 | 2011 | `fdb4220751029eebf9c946e9ba5319671533e4314280dc8bb81f5718dc553fbe` |
| 16 | `fed_statement_20111102a.htm` | `a7283f261996d1d641130a5ec7395b79090b36e4d442620664f09ac0366a9348` | 82945 | 200 | 2026-07-29T02:20:56 | 2011 | `e74e6b79acaa1a4b38f0d2acb4e64d12f04bef7bd7970db9c3e9469cf4b66400` |
| 17 | `fed_statement_20111213a.htm` | `4487709329d693e39ba7b052b5bed72edff3c8e601c5269fbf0d72e7111543cb` | 82588 | 200 | 2026-07-29T02:20:57 | 2011 | `0cd08d40c51062fae5b854436ff72a1a11c7a0bfdc32a0e1becb970425005db9` |
| 18 | `fed_statement_20120125a.htm` | `ad3df2cef8fe5250b96b1c478cda263428f5def92610579452571e03fd896fdc` | 82474 | 200 | 2026-07-29T02:20:58 | 2012 | `11b2c50a11cd5a70f108e93a45148d04c0cf7d639d16901993f7ce4f93e16b46` |
| 19 | `fed_statement_20120313a.htm` | `22165cce172ebcb8b15f20427de1c8a6608a614f52120cdac045df3c25119c86` | 82523 | 200 | 2026-07-29T02:20:59 | 2012 | `aa28e6565548d5aec63cc889293f2cc7f63cae2004fa16dc6b98cda3ab55fd2e` |
| 20 | `fed_statement_20120425a.htm` | `fb9f747a01a072b726b6fd6bf73131159ce5ec0506945dad64faca4766b23933` | 82574 | 200 | 2026-07-29T02:21:01 | 2012 | `3ecd05903ae2511bc67084c42cf5353126dbd3a3bf8a940d61325ab2c2681500` |
| 21 | `fed_statement_20120620a.htm` | `18fd18813557d106f2ed747eebba7c64d31369811ca67e0642da4f607e636a54` | 83684 | 200 | 2026-07-29T02:21:02 | 2012 | `444e3b6e233189c1afb77818ff83337b4e0571270e352272e7ec58ee1c5bc8ca` |
| 22 | `fed_statement_20120801a.htm` | `43562beab4c193bee0ff970f86f9fa6b5b06bdd61c05205599aee2aac2a89a55` | 82652 | 200 | 2026-07-29T02:21:03 | 2012 | `24854ac3f55ae2c53eb2134aa13595d399540dea42fa07d73e839a160a5e052f` |
| 23 | `fed_statement_20120913a.htm` | `98a509b4b7d9fa1b42c100990122268f67e0e22310df28fa0d03cc7dc5e85bea` | 83481 | 200 | 2026-07-29T02:21:04 | 2012 | `857ae5e8c9ab8b20e6205267103e0f8373ef1740971ad207d947d05ae8605c97` |
| 24 | `fed_statement_20121024a.htm` | `52680e389cb01c19efe0402bb9c070dc9dc00522e43574cc2b49738c3c844ab1` | 83465 | 200 | 2026-07-29T02:21:05 | 2012 | `76e60ebf1ab953080ea7997b24a12b1d6e5cbbe72badb459a1ff32f7b9a5b13f` |
| 25 | `fed_statement_20121212a.htm` | `ff7471f88c3e47d6704b40d3235d27d877a93a5803c0f88dc19625859ad647a6` | 84517 | 200 | 2026-07-29T02:21:06 | 2012 | `67580af88ed23c358ad06d98a5a8e002273578feb3fcb79adf218638abcbc715` |
| 26 | `fed_statement_20130130a.htm` | `e76b0cfca3cb1e3a096b4acaccf7635cf5061450be963c04fb5658a1192acf8e` | 84103 | 200 | 2026-07-29T02:21:07 | 2013 | `5dd760027b7a10c12bf76c2656ab79a236cfe2729a7594ac3a311712c6ae2e88` |
| 27 | `fed_statement_20130320a.htm` | `b798533cb43067df7471db95334f924635f7a14facd81b842f52b0eb7617a21a` | 84140 | 200 | 2026-07-29T02:21:08 | 2013 | `a753305d1e5a9661458ec34a513ae8c39e9842c23cd0c8b25acf05a724b188ca` |
| 28 | `fed_statement_20130501a.htm` | `be8f363a19223fd31f1617940f06e63f4e19b73303ba6918f62dfee1a07a62f7` | 84215 | 200 | 2026-07-29T02:21:09 | 2013 | `3f8c68e85381014bb079f64b22015eee750f8ede09aea556668502b17cb39946` |
| 29 | `fed_statement_20130619a.htm` | `d77c49daaf6b679210ef9bbb76fe2ab1c67a6e358fbade543bb9d7aaaae945e7` | 84427 | 200 | 2026-07-29T02:21:10 | 2013 | `4cb93e1ad2c6909a4fe25ad887cb6b1eae8fc1db873573a3f9f458483faadae8` |
| 30 | `fed_statement_20130731a.htm` | `f268ef4619db4b24ad746db9762d52882e60e54b20a8b78912063e81c4704d07` | 84403 | 200 | 2026-07-29T02:21:11 | 2013 | `87b286fd34e203b5d8581077b7edc12bff1434c4fd4076dc13afadb9c2e2b5b1` |
| 31 | `fed_statement_20130918a.htm` | `d6a6059b9b299bc1b7aaa299238d6fe9aadc38b869c3730a3d85493c57a9097a` | 85071 | 200 | 2026-07-29T02:21:12 | 2013 | `c44435361de84c36070f93140413cfb310460e020d0148b0b2bc48d49d7d5c07` |
| 32 | `fed_statement_20131030a.htm` | `4753b841529dd7feb37c91702c60411cfbc4843782705a737f05d1892cffac44` | 84940 | 200 | 2026-07-29T02:21:13 | 2013 | `d2ac988035f88da254195c8f017da515de330e97a9a34402f3f7b460f4a2affa` |
| 33 | `fed_statement_20131218a.htm` | `68aa3ebf78f5b53aab7d91956062124f56dc78339f2fefa81b39023632b9be7f` | 85728 | 200 | 2026-07-29T02:21:15 | 2013 | `f704f237b1affa6c781e5a05eb8c2c3cc87e66af714af2a543e071c2bda7f484` |
| 34 | `fed_statement_20140129a.htm` | `4cf2e66aed6408ded26542817938af111e9d065294da5311032a1e4e703de5de` | 85653 | 200 | 2026-07-29T02:21:16 | 2014 | `a306d80fcbbc784ec665d49ff8d19702c103a298c1a7b95aad2f4e8be714685a` |
| 35 | `fed_statement_20140319a.htm` | `78d024251087d1b5673546d98d56991369c32f6f84c2de07041731ffc5b51e5d` | 85949 | 200 | 2026-07-29T02:21:17 | 2014 | `7354f3881c74e0fe8203d9856d76876c8c528aa38acab4563d95fb6ce92eadb0` |
| 36 | `fed_statement_20140430a.htm` | `62098a27c474618c355e701358422d4bb775a1fa148ce6afbb7bd9e35b3aa7f1` | 85437 | 200 | 2026-07-29T02:21:18 | 2014 | `c511522b0cce6c9beb5f9aab92bd31642aa1bd186e0cf2e26512604aaf1547e4` |
| 37 | `fed_statement_20140618a.htm` | `977c4ed36ae47617bc4497b1099f75c9637dce7ef77d32738343a8af8f31343f` | 85367 | 200 | 2026-07-29T02:21:19 | 2014 | `612291c61458e80cacad40e58f2c57aff55b1f3dce1485140d009bc0487e2641` |
| 38 | `fed_statement_20140730a.htm` | `fabc9197508c15327127c1cf4ece5175f119bc45162e5f144823c034ffa3e8a2` | 86286 | 200 | 2026-07-29T02:21:20 | 2014 | `061848806b9b21b514842dac999dbb6cf4deced865c24633d2872144bd41bcdf` |
| 39 | `fed_statement_20140917a.htm` | `ee9a3aa3afd5b81b443e6432ee8ab731f3e31386a3929b0814012fd090e7d65e` | 86015 | 200 | 2026-07-29T02:21:21 | 2014 | `456bddad0fd7f5378c3b3565407237347f3f0c8d2044f8dbe12752279323077e` |
| 40 | `fed_statement_20140917c.htm` | `c6d0361c09b97dce500a3bcf651cab8986d96d8f1426e345e2026cec361334f9` | 84245 | 200 | 2026-07-29T02:21:22 | 2014 | `-` |
| 41 | `fed_statement_20141029a.htm` | `705132e5724bc4a31006a7fe76b69ab54cf16367bcd526a0910a914cc72f004c` | 85398 | 200 | 2026-07-29T02:21:23 | 2014 | `b48d30398b5bf9a1129122a6c232f3f0efa8b47880521664ec1bc99b495718bb` |
| 42 | `fed_statement_20141217a.htm` | `9aea0850d18094006c115211ea3ec3f5e8166de307549217cb5ad82a506ca8c0` | 84752 | 200 | 2026-07-29T02:21:24 | 2014 | `38ddf9d732994a2db72edf7b88b12c60f4197447b4ea61352af869ad3587e790` |
| 43 | `fed_statement_20150128a.htm` | `8dc2983d5bef39216728c2431a1fc522ef935d2bef8f7f8cf3cd25d58ca42b6f` | 83753 | 200 | 2026-07-29T02:21:25 | 2015 | `56910b5bc8c9400153a444dffe5aad972a2ab2f29eea97e3bfd1982cf1e9d5e9` |
| 44 | `fed_statement_20150318a.htm` | `5ba18dd6c52195df8004d8067eed6db3cea1bc31fa44bac73c1996a22c1bfe83` | 83666 | 200 | 2026-07-29T02:21:26 | 2015 | `5bc7c9c4004bdc24a775de2ebd55ab2118ace752468e2145f13a7d515e5d870e` |
| 45 | `fed_statement_20150429a.htm` | `4da6bcf6f2fabcece171e3928d09096d1e0edda3a16fdc7aa5036a379602de30` | 83557 | 200 | 2026-07-29T02:21:28 | 2015 | `e51852343a1c1777ff042fab4cacd357ed444d0420a247cc67f251a721eac3a7` |
| 46 | `fed_statement_20150617a.htm` | `4cee8a2db866378ed6a4100b4acc4a588af20682f24c4021b9a69869656f9423` | 83413 | 200 | 2026-07-29T02:21:29 | 2015 | `cd3b2de49ef43db31debfd1e6d3c852be00a65934bb66d74c8d6884852c51e54` |
| 47 | `fed_statement_20150729a.htm` | `0f224fa63cfdc61da44a2934173518ec83f2d0e8dd42b8813865813c182a30ba` | 83382 | 200 | 2026-07-29T02:21:30 | 2015 | `14cb4ca5e2244618db8c0919585a65fe9a4f167afd4191787786511053568ea0` |
| 48 | `fed_statement_20150917a.htm` | `7d0271b94aebc970e73ab0fa495893e1bac58435f0c4a0f1d184d3e52a56a2d0` | 83683 | 200 | 2026-07-29T02:21:31 | 2015 | `9df897962f8118066c50564acf08c7f5c9576f7c9873a6861b7e55440eb7782e` |
| 49 | `fed_statement_20151028a.htm` | `65cc3f5a4b8c4ede0602ea67cb86e7f79ec5df303746807444c8dfc5646e8518` | 83593 | 200 | 2026-07-29T02:21:32 | 2015 | `c0caf7d221cb95f42d3b381641a092999eaeb2415d99efab3005a4bbf9ef39e1` |
| 50 | `fed_statement_20151216a.htm` | `102a7ae9703fbab3231665a98a09d4091e471e470f110f5c52c52ec8365c669a` | 83621 | 200 | 2026-07-29T02:21:33 | 2015 | `da40a1219cb7e1fa3df9e9b5003c2a1a54b34781791410a790530baccdd5ef31` |
| 51 | `fed_statement_20160127a.htm` | `c29ba2a07cf4c5e7213bdbbf1bb83f1d15cde97bd79aba2c7a27620d9ba32707` | 83480 | 200 | 2026-07-29T02:21:34 | 2016 | `8da296fb3f810c7a7c88a5d37fd7b60386701d76cbbf924b6eccbc7a58ea5c3f` |
| 52 | `fed_statement_20160127b.htm` | `2d49015a2dc2896e0b6af2c06611fc1b86e43dcbabe6f2b52525b950c48e82e6` | 82285 | 200 | 2026-07-29T02:21:35 | 2016 | `-` |
| 53 | `fed_statement_20160316a.htm` | `04636b56982afc7fb19bbf362cdcbcaa87410d175b47a28b1d0479cd473c89c9` | 83538 | 200 | 2026-07-29T02:21:36 | 2016 | `f6a01c185fafc7b2e3a103c2c5ab5e29e3d88110378a9fd04101116c7a33f260` |
| 54 | `fed_statement_20160427a.htm` | `af37af1363ec85dc1d88d48d7f0aa2e401b3c27b356d2b9372e53f30dde148d3` | 83564 | 200 | 2026-07-29T02:21:38 | 2016 | `7cb6b7917bea041217df5c86790f658d326ecd3a041832b8d0b75432a4e1e09b` |
| 55 | `fed_statement_20160615a.htm` | `c13be6ead211981a19c32f41ebf4b6d2089246358e042abdf23d4ba6d9551773` | 83334 | 200 | 2026-07-29T02:21:39 | 2016 | `bd6aefabb7b4b12a584996ba6a68b5fa6e2ae83b6baa894c14284ef425ff57a3` |
| 56 | `fed_statement_20160727a.htm` | `43ee87b4f474b912668f7bedf4942efdea7dc6fb397b23c3065ae19ebac5ab65` | 83478 | 200 | 2026-07-29T02:21:40 | 2016 | `8b6d0cd2674e983b64fcc0414f9d2f6afe3b58373d096db17cfebcaf208958a6` |
| 57 | `fed_statement_20160921a.htm` | `3aab036f7e1585dc421152c517666d2a709898597fc63dee75fd78ae771e53b4` | 83694 | 200 | 2026-07-29T02:21:41 | 2016 | `eae841ed473b65ef55c9c2c99a0398b51d7f82c690c9e9ba9ed48754c2284523` |
| 58 | `fed_statement_20161102a.htm` | `03e5fa223b043bbe80adba23742e42ff866d49a09671d4656bef899f0391074c` | 83666 | 200 | 2026-07-29T02:21:42 | 2016 | `c4184ae03cd213e03f12b1a3ffad0caf0c702a6b223519b2e31a33b52889e8ed` |
| 59 | `fed_statement_20161214a.htm` | `3859d82ea3fac0a80e50033dbce2823144204d0c65f1646f07fb1ae65bb40fed` | 83325 | 200 | 2026-07-29T02:21:43 | 2016 | `f436c1d75a2fde51f2fabf78b74d8f943ae6c536791cec7f238b84d44ca1a789` |
| 60 | `fed_statement_20170201a.htm` | `7b537db73fca90de962d1415b056a789d4ed0eef9e8f6dce79b08af649a73a1f` | 83773 | 200 | 2026-07-29T02:21:45 | 2017 | `ba1c4e4eb679fed2d484212eee253a5a7bf0e7eeda8277de387fc5bd34cdb1e9` |
| 61 | `fed_statement_20170315a.htm` | `3831a0216f24ebf432d4fdf5a2031c7f5f7b21571fa8a0d366ddf80a98306e88` | 83508 | 200 | 2026-07-29T02:21:46 | 2017 | `28938725a66018fd59038f42c98ea5a8f6177de7daa39f96f2e57a0620e4d35f` |
| 62 | `fed_statement_20170503a.htm` | `a238c4939137aae15c435339cd17a4136ce1765d7da4e63ac26317fbf0a0cba0` | 83489 | 200 | 2026-07-29T02:21:47 | 2017 | `8586261dbe8ae0fc58c032f49ac055fe613845c5e707341dbdfaf269ef0319df` |
| 63 | `fed_statement_20170614a.htm` | `98a0114fb32ab9e31d07dc1f5ffb4c456c56f906c87f892659e7f426a5078c94` | 83685 | 200 | 2026-07-29T02:21:48 | 2017 | `9964b6a36db5437925a5ffe4f41ce86dfd2fcff13c7b6697454916ac4708b987` |
| 64 | `fed_statement_20170614c.htm` | `2a5c2327de3c106d7b37a87bcf643c54f23a27705200d5459013b08df7df0df7` | 84252 | 200 | 2026-07-29T02:21:49 | 2017 | `-` |
| 65 | `fed_statement_20170726a.htm` | `1662196e866e4b330e87a1a1766f2ae509fde02a474545af3928816fe1545efe` | 83373 | 200 | 2026-07-29T02:21:50 | 2017 | `d1809e29908d994c87a49d807876d68a81af425d518dc0e04854dd4a26ca831e` |
| 66 | `fed_statement_20170920a.htm` | `09603388e305046b5590bb6bf850728e4d419067d1f97d96cb765750257a856c` | 83549 | 200 | 2026-07-29T02:21:51 | 2017 | `bc1e86f06ddde7109fa13c10d352721a8fc36960749532f7eb1546f9e2c65ef1` |
| 67 | `fed_statement_20171101a.htm` | `3a7471982c7a4681beb17f1e8a8bc89222ee600643113794d4c53875a8ffa507` | 83429 | 200 | 2026-07-29T02:21:52 | 2017 | `051bee3b61ff4aab5d4889e63413978099fc3591ed18d3c0cc478abb6ac5a840` |
| 68 | `fed_statement_20171213a.htm` | `beb40bad4f6540b86ea87c157eed77a7c89df169a3d8a122c9fc7560283fdfd7` | 83208 | 200 | 2026-07-29T02:21:53 | 2017 | `9777ac6fa415929204b75444292924e3db9d6471797b6ff0c4b57156586917ea` |
| 69 | `fed_statement_20180131a.htm` | `bd4910df2783e34a75ba771cc69dd99940b9c98c1fb52554cd9a456d9411d405` | 82749 | 200 | 2026-07-29T02:21:54 | 2018 | `3ab3ee44be1f11d1bb4aceac422faf97c53d9579394fc7f39e80cf648d33e9b0` |
| 70 | `fed_statement_20180131b.htm` | `2086a1804195a77f7bbe564f9a652aeaa5c370c3cd142d4e57591e5f05dcd79a` | 81205 | 200 | 2026-07-29T02:21:55 | 2018 | `-` |
| 71 | `fed_statement_20180321a.htm` | `dd542049d7521a97d39f1c215256b497798b546038e56439d91ac18be94c9ffc` | 82910 | 200 | 2026-07-29T02:21:56 | 2018 | `14983746fded83ac4e195f22020a05e4415e178b51438208248559a73342ca90` |
| 72 | `fed_statement_20180502a.htm` | `1ed0c93654b01ccb40c3f57ef808528715c30f6c633db4a561762283c2580364` | 82726 | 200 | 2026-07-29T02:21:57 | 2018 | `4cc8275d6bb4cbaec1fb08dbc56e4569229f11cf96e0e2b223cbc305c75f0317` |
| 73 | `fed_statement_20180613a.htm` | `654b3d832aa3116f13b6a4f6eb1c36d5ac926f060d52a34aead77a435bfdf619` | 82088 | 200 | 2026-07-29T02:21:58 | 2018 | `8f693ecf6a952593950f538d85d1072e4e84b52f418a8450a0cbff30d1fa1f56` |
| 74 | `fed_statement_20180801a.htm` | `47d3995822c0e117ef8376b898de358a97c34b5359560a50cb2a8aebb9e2ad97` | 82029 | 200 | 2026-07-29T02:21:59 | 2018 | `92e8327c5d5b4cad0dae75e5fb800fa56fddb7d47173f5ccb8ee4c6c5d61067e` |
| 75 | `fed_statement_20180926a.htm` | `a7b41726cfe4b14475664bc3a9d384b11fadbb2cb69b3711e2e768d17abb804c` | 81908 | 200 | 2026-07-29T02:22:01 | 2018 | `1e810e7576b1df7d6cac0fe5efc9b1ffb78aa2ac3ddf2c44ac0334a148d7ec8b` |
| 76 | `fed_statement_20181108a.htm` | `b21662dc2d7bbadee44b914872ec48b25777cef08ab4c3b7992a8d5b1178a308` | 81982 | 200 | 2026-07-29T02:22:02 | 2018 | `b60126b9e3f4fdb3a498d0e9d71d15737d777fea97667b3d0434ef5734873bb3` |
| 77 | `fed_statement_20181219a.htm` | `8fda2f4bf59b236fa9709fda1ebdc06bdf6bb3819d846b7059445752b8025519` | 82169 | 200 | 2026-07-29T02:22:03 | 2018 | `2a818fa8de5a675ddbe09674789c9619eaf2aece64edb718619ab45ed22d5a7d` |
| 78 | `fed_statement_20190130a.htm` | `fba666ec30ae6482cb2be1f40fbe4de2c2b5b75410a0fc0d4962ca5ffb3f099a` | 82155 | 200 | 2026-07-29T02:22:04 | 2019 | `07e33f32b86e891b877714bf94d519d021eadfe57f264469c27c2475a9468782` |
| 79 | `fed_statement_20190130b.htm` | `fb55f23bcb4f023264b26357a6a7e5e6c9c6ae5c0cc01210f1429f78530c4f8d` | 81155 | 200 | 2026-07-29T02:22:05 | 2019 | `-` |
| 80 | `fed_statement_20190130c.htm` | `ad7b6a7caf2391979bf87aa8c0282e58ef72d5c21f95a217de09cf766e3d574a` | 81424 | 200 | 2026-07-29T02:22:06 | 2019 | `-` |
| 81 | `fed_statement_20190320a.htm` | `ff9a15b6defcb1dd49c45ffb9211b601c1bd1db74f2fe33cde675b82541a7329` | 82248 | 200 | 2026-07-29T02:22:07 | 2019 | `de49446ab2ab931fa48ea7d0cdf606308b0a24c89cca299df252723babe3e4dd` |
| 82 | `fed_statement_20190320c.htm` | `aca7977c3fee991e826beb03b792d60b4b1e1f7bd049f0cd7b2fd4d73f3a3df9` | 84139 | 200 | 2026-07-29T02:22:08 | 2019 | `-` |
| 83 | `fed_statement_20190501a.htm` | `cf11a7bf38fe115f27744b74286ca25117dc0a94b30c7c2545aa5722d7281117` | 82078 | 200 | 2026-07-29T02:22:09 | 2019 | `4b288b17cdeb307aa8ea768e2583bbdb081797ef0bdd3a2d4625f6a74ac998b1` |
| 84 | `fed_statement_20190619a.htm` | `e0dcb4776867ac79db4e3dac29d28439d2be63b1e2d24f87e3e158a3bea838db` | 82320 | 200 | 2026-07-29T02:22:11 | 2019 | `dc66922027696b675f86548180f7ecce529aa1f22d3ef25b1b78a23f4d6c61dd` |
| 85 | `fed_statement_20190731a.htm` | `e731f36cf183ba454e7f62e447ab2fb7fb8b53ea3e6d23b28a60756f962e2871` | 82608 | 200 | 2026-07-29T02:22:12 | 2019 | `9632a1f6e85e310bbcae145adf5ed3349d9be08a28e7f0a0b0b7101c59b28370` |
| 86 | `fed_statement_20190918a.htm` | `75433b9823377b2a357d16c2d4a833a11620bce4b2c4c6481d81ad5d6ecadcc6` | 82504 | 200 | 2026-07-29T02:22:13 | 2019 | `a133dda83f0d344b11343527b33ee0d5829d5297eed7930d52eab4a7b7af8a01` |
| 87 | `fed_statement_20191011a.htm` | `52ce30b32e5a6b45167e8a183bd8765a62157f03490637c560d690f811850cab` | 85772 | 200 | 2026-07-29T02:22:14 | 2019 | `a4c9c485379e009609bd3f5847566be5661de9af8082d1cc70031e623741d7e4` |
| 88 | `fed_statement_20191030a.htm` | `8d1cdbbeab2372620e24ec59b28bf6041e94314eed47ba9a5ae5b4b30a16872a` | 82275 | 200 | 2026-07-29T02:22:15 | 2019 | `2a318ae4b687376e3ee51112bdcf971b9ee5a33825fb371236cd8a866362cce2` |
| 89 | `fed_statement_20191211a.htm` | `e396dfe1ab2dca3cc28950f4bc978971849a9613cb6986c5e5f477ac7fa0379d` | 82073 | 200 | 2026-07-29T02:22:16 | 2019 | `1b80fb8395406de564670d4cf6a15ee0e540505f8e4542ff21e24ed41bb30456` |
| 90 | `fed_statement_20200129a.htm` | `6b6f612ae46e170355ef4c753d31766613640547e9ef50f48feedd7973d2d691` | 82079 | 200 | 2026-07-29T02:22:17 | 2020 | `83ab2e265c47884fe55b162ff3f85ba04f4b6ea0e2e4244361610f2e8610f0cf` |
| 91 | `fed_statement_20200303a.htm` | `3ad38e7dca94e2bf1eb3ad8baa2229ceb76a773c6606f89c10e0c31a8803c6c5` | 80778 | 200 | 2026-07-29T02:22:18 | 2020 | `8b87e548fb0c6f5779144d7306e381abb1efb3689b18ea3075543273bc894bb3` |
| 92 | `fed_statement_20200315a.htm` | `d0026d855c12698a42a1a63bc41e7ff3cb480e353c2949c5f91d2a05b2726818` | 85154 | 200 | 2026-07-29T02:22:19 | 2020 | `6611690d7a9962fc904a8ddcef6e79fd0925553f533e4bfcee33c17b11aa426e` |
| 93 | `fed_statement_20200319b.htm` | `e74b7a031a4964881831d2e1f3546af4bfbe71c5479148535e502325d6bcf61e` | 82172 | 200 | 2026-07-29T02:22:20 | 2020 | `-` |
| 94 | `fed_statement_20200323a.htm` | `3ee1150da68cfeb3f347af6825b1f1d22c2c9e08757927bfd92fae1bfa935a97` | 85027 | 200 | 2026-07-29T02:22:21 | 2020 | `cd2676bbe6f453ed021d6dad2e226d9e6c039ccbd9eb86fa44d0cb66c80d07d2` |
| 95 | `fed_statement_20200331a.htm` | `f8d1d314ec475b6a8b5ed62b6f8c064bb77b290f748fa5eb9698aa4111ae99ab` | 82569 | 200 | 2026-07-29T02:22:22 | 2020 | `-` |
| 96 | `fed_statement_20200429a.htm` | `61589525de9f5bb415e6fcd98b3fd53f3f753b846b8e9b743686cc4ecfd38b10` | 82800 | 200 | 2026-07-29T02:22:24 | 2020 | `7784ce15dcfbb8ec8a77fc9217ff64edb71571b3329ee642103bc80d8ab2044e` |
| 97 | `fed_statement_20200610a.htm` | `9759d297d94564319ac52c06094cf66d77b08e06aa764a12c9876bd00f249ab6` | 82796 | 200 | 2026-07-29T02:22:25 | 2020 | `8f6f6626b4ad0b3efba86a59a071ccbff2d2f83d51845a8bc054e5445c41b8b7` |
| 98 | `fed_statement_20200729a.htm` | `dcea9aa9a75e90d84a555df661832957d5bc5b743c367a72b21aa0d7bcb6d6f9` | 82936 | 200 | 2026-07-29T02:22:26 | 2020 | `8d2593717a2fd698ac45e8054d84f682672fb61fd5bc397dd8a0209d38c17cd3` |
| 99 | `fed_statement_20200827a.htm` | `4c5699828d05d3f1572305110b9b8ca06c7e67c7313043e37c89fdfd92ac27c9` | 85930 | 200 | 2026-07-29T02:22:27 | 2020 | `-` |
| 100 | `fed_statement_20200916a.htm` | `b1207365f22d298811de8bcc4bcc27e35a4a72729fd8fb4df0c104e5ec2eb061` | 83554 | 200 | 2026-07-29T02:22:28 | 2020 | `fade6dcf72252563532cb5e29a41ddb3371310a4735e2be5cdc96d54a06cae07` |
| 101 | `fed_statement_20201105a.htm` | `50883634ee50edc19fd9ae4e13ba686939b96c2f64a3fb6c610e8b50c7692113` | 83013 | 200 | 2026-07-29T02:22:29 | 2020 | `d6443712ae7898aea68b027147eb7444bbf0c557518f683e62d6ca5342c161c4` |
| 102 | `fed_statement_20201216a.htm` | `e71966e09a72ccddd5c54559cccbac873ab562e1f16bfb61a999bad8ce4c0249` | 83124 | 200 | 2026-07-29T02:22:30 | 2020 | `eb8d8208f6330bbffc94a9fa5ecee929aa5a758e7b4ff516506cee85a300d212` |
| 103 | `fed_statement_20210127a.htm` | `18598f8a69eae624feb23f92b3fae546a0e5272461ae8b2cff13c9272e756afd` | 83195 | 200 | 2026-07-29T02:22:31 | 2021 | `274be0ada403ac4726d968b10e0bf9f20d83cbf373c418fc6dfaf518462dccb4` |
| 104 | `fed_statement_20210127b.htm` | `7ed967da67208e0b1c25b90ec8d8d3528f1674643fe3ac3c5829fc4c49929a5c` | 81103 | 200 | 2026-07-29T02:22:32 | 2021 | `-` |
| 105 | `fed_statement_20210317a.htm` | `3271c495d3a94cd8b0a887617ecb7e7786a4adb529ebc9078b7e8896caf0338b` | 83157 | 200 | 2026-07-29T02:22:33 | 2021 | `50042afddf3d541c1f3fef2d6ff6e85f8b639e0a6b20c59dd17c4bbed9f5cec5` |
| 106 | `fed_statement_20210428a.htm` | `7ca0a33d41112292f260efe2ae6c85dfdc94a548dd107ed31e10b73da6618ccf` | 83145 | 200 | 2026-07-29T02:22:35 | 2021 | `16a5013e6a121a878ad4b6aa0e7a6bcdadba6cb7f0b98563e226bca2c4aec3cd` |
| 107 | `fed_statement_20210616a.htm` | `8552ed3e423d16b64a2fb2774be0543d3cace2dd7dc20beba57fd2acaebbbbf4` | 83105 | 200 | 2026-07-29T02:22:36 | 2021 | `8a62048e65617ece7ff1cdef0bbb7b74e69f595a2564dc51ffbab87ee132db99` |
| 108 | `fed_statement_20210728a.htm` | `149c6b2ca48aaf95c4fa2c876878974fa7a5ef3a27b37d88a20875d53cfe6ec2` | 83188 | 200 | 2026-07-29T02:22:37 | 2021 | `3953c83b28d56449e4ef3e54641850452aa235074020549e0eb85fb272081e31` |
| 109 | `fed_statement_20210922a.htm` | `26b08b7d327ba94ca5778461a7deae72c35f8ca56e7dc2795849cff4c6601d27` | 83307 | 200 | 2026-07-29T02:22:38 | 2021 | `cb547b0de1eace0cca7006af9c350e46c43cdd306978789290f6015a6274e347` |
| 110 | `fed_statement_20211103a.htm` | `c6cc384f96e6ce403c86ee576d733816d62d6716be3d81b4265d79f31dd90d9c` | 83986 | 200 | 2026-07-29T02:22:39 | 2021 | `5f7e7f552fcf64200cd167b58bd7457c8ea4f24b1b88c66c49f55943e13616ca` |
| 111 | `fed_statement_20211215a.htm` | `5e57b93349cdd8e30491c51657598bd71b2ea18c7a6ff61ca50b48fec645cada` | 83382 | 200 | 2026-07-29T02:22:40 | 2021 | `ed37004ea4087247d531dcc8a2a40a69219ffd7dd5b4aacb6e318e8602d389e0` |

## 8. 待 Aaron 批复的决策（SA-1 不得自行决定）

| 编号 | 问题 | SA-1 已做的事 | 决策包 |
|---|---|---|---|
| D2 | FOMC 采用会议日还是 statement 发布日 | 两类日期都已提供，`is_fomc_statement_day` 区分 | 既有 TASKBOARD D2 |
| D2a | FOMC 条目类别筛选（例会 / conference call / unscheduled / notation vote） | 全部如实收录 + §5.3 完整分类表 | `DECISION_PACKET_F10_D2A_FOMC_ENTRY_SCOPE.md` |
| D3 | 停摆延期发布如何编码 | 按官方实际发布日记录 + §5.2 | 既有 TASKBOARD D3 |
| D4a | FOMC 2010–2015 发布时刻无官方记载时如何处理（项目级 D5 已被 symbology 占用，故编 D4a） | 填哨兵值，未猜测 | `DECISION_PACKET_F10_D4A_FOMC_RELEASE_TIME.md` |

D1（同日多事件编码）与 D4（缺失年份 fail-closed）不阻塞本表：
前者由"每事件独立一行"保留全部信息；后者未触发（无缺失年份）。
