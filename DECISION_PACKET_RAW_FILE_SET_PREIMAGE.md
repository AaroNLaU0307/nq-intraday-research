# [RESOLVED 2026-08-01 — 机械事实，非方法决策] DECISION PACKET — raw_file_set_sha256 的 pre-image 约定（SA-7 / F-07）

状态：PENDING_AARON_APPROVAL（来源：SA-7 runner 硬化，规格外歧义停项）

1. **问题**：授权包 §4 把 `raw_file_set_sha256 =
   08fca11b7a9aea1f96f740409c099696e48907a408f409dfbadd82c5ac584298`
   锁为硬门输入，公式写作 `SHA256(sorted(relative_path|size|file_sha256))`
   （139 个 A1 dbn.zst，总字节 58,711,328，成员 hash 取自官方 manifest）。
   但**该公式没有固定序列化细节**，而门的通过与否完全由这些细节决定。
2. **未定的六点**：(a) 记录之间的分隔符（`\n`？无分隔？）；(b) 是否有
   结尾换行；(c) `relative_path` 相对哪个根（job 目录 / archive 根 /
   quant-data 根）、分隔符是 `/` 还是 `\`；(d) 排序键（拼好的整条记录，
   还是仅 path）；(e) size 的来源（官方 manifest 声明值 vs `os.stat`）与
   格式（十进制、无千分位）；(f) 编码（UTF-8）。
3. **可复现性**：仓库内**没有**生成 `08fca11b…` 的脚本或记录——
   全仓 grep 只在授权包与 SA-6/SA-7 任务书里出现该值；`quant-data\tools\`
   下亦无。因此无法从留痕反推 pre-image。
4. **SA-7 无法自行验证**：确认唯一办法是照某一约定实算一次，需要读取 A1
   官方 manifest 与 139 个文件的 size（纯元数据，不解码任何 dbn.zst）；
   本次任务的硬约束是"不读真实数据"，故未执行。
5. **已落地的实现（fail-closed，不阻塞其他门）**：
   - `scripts/s0_real_run.py::compute_raw_file_set_sha256(entries)` —— 纯
     函数、零 I/O、有单测（顺序无关、改名/改 size 必变）。当前假定约定：
     记录 `f"{relative_path}|{size}|{file_sha256}"`，`sorted()` 整条记录，
     `"\n"` 连接并追加结尾 `"\n"`，UTF-8 编码；`relative_path` 取官方
     manifest 的 `filename` 原样（即相对 job 目录），size 优先取 manifest
     声明值、缺失时回落 `os.stat`。
   - 门 `raw_file_set_digest` 先校验文件数 139 与总字节 58,711,328，再比对
     摘要；任一不符 → Stage A 失败 = `PRE_RUN_ATTEMPT_FAILURE`（**不消耗
     exposure、不烧 trial**，可原地重试）。
6. **风险**：若上述假定与当年生成口径不同，该门在真实 S0 首次尝试时会
   稳定失败——安全方向（宁可挡住），但会白跑一次 Stage A（含全量 pytest
   与 seal_check），且必须在授权窗口内改代码，破坏"授权 commit 冻结"。
7. **Option A**：Aaron/main agent 在首次真实 S0 **之前**用一次性脚本按
   §4 公式实算并公布 pre-image 约定（连同 139 条记录的前两条样例），
   SA-7 假定与之对齐后固化进 IR。推荐。
8. **Option B**：把 `raw_file_set_digest` 降格为"披露不设闸"——只计算并
   写入运行目录，不作为硬门；文件数与总字节仍设闸。（弱化包 §4，不推荐。）
9. **Option C**：授权包重渲染时把 `raw_file_set_sha256` 换成一个有脚本
   留痕、可复算的定义（例如直接对官方 manifest.json 的 bytes 求 hash——
   该值已作为 `d8d1edc7…` 锁定，等价覆盖"无缺失/新增/改名/替换"）。
10. **问题**：批 A（公布并固化 pre-image 约定）、B（降格为披露）还是
    C（改用 manifest.json hash 覆盖集合完整性）？在批复前，
    `raw_file_set_digest` 门保持 fail-closed。
