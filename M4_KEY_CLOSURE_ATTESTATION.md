# M4 KEY CLOSURE ATTESTATION

独立收口文件（Aaron 2026-07-31 指令）。本收口全程未发送任何 Databento
API 请求；未以 401 探测"证明"撤销（401 不能唯一归因）。未运行真实 S0。

```yaml
key_revocation_attested_by: Aaron
key_revocation_attested_at: "2026-07-31 (Aaron statement in-session:
  临时 key 已在 Databento 后台撤销; main agent records the statement,
  does not and cannot independently verify backstage state)"
user_registry_variable_present: false
machine_registry_variable_present: false
new_process_environment_variable_present: false
repository_secret_scan_matches: 0
```

## 机械验证记录（方法与时间线，UTC）

| 时刻 | User 域注册表 | Machine 域注册表 | 当前进程环境 |
|---|---|---|---|
| 2026-07-31T07:23:48Z | PRESENT | ABSENT | PRESENT（应用启动时继承的惰性副本） |
| 2026-07-31T07:25:59Z | PRESENT（首次删除未生效——对话框未确认） | ABSENT | PRESENT |
| 2026-07-31T07:29:56Z | **ABSENT** | **ABSENT** | **ABSENT** |

- 注册表验证方法：`(Get-Item HKCU:\Environment).Property` 直读变量名清单
  （值从未被读取或显示）＋ `[Environment]::GetEnvironmentVariable`
  双域交叉；HKLM Session Manager Environment 同法核对。
- 进程环境 PRESENT→ABSENT 的跃迁证明 Claude Desktop 已在删除后完全重启
  （新进程树继承已清理的环境），惰性副本已清除。
- fail-closed 记录：第一、二次检查因 User 域仍 PRESENT 而拒绝出具本
  attestation，未预先填写期望值；第三次全 ABSENT 后才生成本文件。

## Secret 扫描（2026-07-31）

- git tracked 全量：模式 `db-<10+位>` / `Authorization:` / `Basic <b64>` /
  `x-api-key` —— 真实密钥值命中 **0**。唯一匹配为
  `scripts/m4_sa1_security_audit.py` 中扫描器**自身的正则模式定义字符串**
  （自指假阳性，非密钥，如实记录）。
- 全工作树（含 untracked，excl. .git）367 个文件：密钥值模式命中 **0**。
- 历史会话日志/异常记录：D5 会话的 401/504/422 异常文本均不含密钥
  （databento 客户端异常只含 URL 与文档链接；已于收口报告 §4 扫描记录）。

## 结论

M4 key 安全收口三要素齐备：Aaron 后台撤销声明＋两域注册表与新进程环境
全 ABSENT＋仓库密钥扫描零命中。M4 至此**正式完全关闭**。

真实 S0 仍未授权。下一步（待 Aaron 指令）：main agent 提交一页
S0_REAL_RUN_AUTHORIZATION_PACKET（锁定运行 commit、输入 hash、正式 trial
编号、输出目录、失败处理），由 Aaron 明确回复"启动第一次真实S0"后方可执行。
