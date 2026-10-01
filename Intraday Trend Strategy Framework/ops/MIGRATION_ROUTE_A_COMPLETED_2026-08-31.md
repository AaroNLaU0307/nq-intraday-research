＃ 迁移 Route A —— S0–S7 完成记录

```ini
RECORD_TYPE=EXECUTION_EVIDENCE
DATE=2026-08-31
AUTHORIZATION=① Aaron 逐字回贴（形制乙，OD-4）· ② Aaron 单独一句「迁移 ② 执行」
S7_VERDICT=PASS —— 静默期 F1 在此结束
S8=NOT_MET —— 本机只有 C: 一个卷，如实留成未满足
```

## 定位符

```
O0  51fa5192d5b24803a8883a7f3a99318c69e81255   旧仓迁移前 HEAD
O1  b8bc8665ff0b284e7c6913cc0aaddb3a780464ee   parent==O0，含 S5+S6，message 记 N1
N0  378e95c8f6a243630841f9cd212d4f3f6a698b2e   新仓 init，不含 registry
N1  e71e54fea3e01244340e4d0364bdbfbc53a1ef23   registry 抵达，message 记 O0/SHA0/行数/末行/两仓定位符
SHA0  ee9da33fdbb47725dc036243adc76d7d9ba69ff06df0df443b09103f897353d6   6697 bytes · 37 行 · 17 事件
见证  registry-witness/itsf/WITNESS_S1_2026-08-31.json  sha256 97ab6b732af7dfc3…
```

## S7 逐条（F4 双向）

```
新仓 ⊇ S1 见证       17/17 事件、末行在、计数口径随见证同行
新仓 == SHA0         ← 单向超集判据放得过分叉，这一半才挡得住
两仓 blob == SHA0    新仓 N1 ✅   旧仓 O0 ✅
交叉互钉             N1 记 O0 ✅   O1 记 N1 ✅
冲突副本重扫         两侧 NONE
墓碑                 被边界点名拒绝；生产读解析到新仓且 == SHA0
全量套件             4900 passed / 455 subtests / 0 failed
```

## 计划之外、执行中发现的两件

**一、行尾。** `git init` 后 git 警告 `LF will be replaced by CRLF`。
`core.autocrlf` 在 **system 级为 true**，两仓都继承；registry 是纯 LF；
本仓靠 `.gitattributes` 的 `* -text` 活着，**新仓没有**。
没有它，新仓将来任何一次 checkout／clone 都会改写字节，**sha256 不再等于 SHA0**。
**它不会在迁移期间发作，会在别人 clone 时发作，那时 S7 早已通过。**
已作为 S2b 落地（逐字节复制本仓的 `.gitattributes`，另加 `core.autocrlf=false`）。

**二、测试侧路径构造 —— 而最危险的不是变红的那七个。**

单一构造守卫（不变量 5）只走 `src/` 与 `scripts/`，**从不走 `tests/`**。
迁移清单据此认为只有两处要改，实测是 **12 个文件 26 处**。

`test_mc_supplement_integration.py` 有三处读 registry 判断有无 `SUPPLEMENT_` 行。
迁移后它们读到墓碑 —— **墓碑解析干净、零行，断言平凡通过**。
**测试全绿，守的东西已经不在了。** 抓到它的不是设计，是旁边一个测试
恰好断言了「real registry 必须有编号行」。

守卫已扩到 `tests/`，注册表**由 walk 生成**。
（我第一版是**手打**的：按 grep 写了 7 个文件 8 处，实测 12 个文件 29 处 ——
手写镜像，写在「因为手写会走味」这个守卫的正文里。）

## R4 的证伪器：**已执行，未触发**

裁定说「若 S4 交叉互钉不足以让冷读者单凭字节完成跨仓解析，则桥的设计须回决裁层」。
**做了一次真冷读**，只用盘上字节与 git 对象：

```
1 旧路径是墓碑                                    ✅
2 墓碑点名新仓路径 / N1 / SHA0                    ✅
3 O1 的 commit message 重复 N1（committed 字节）  ✅
4 到新仓：N1 存在且 blob == SHA0                  ✅
5 N1 回指 O0，且 O0 的 blob 是同一批字节          ✅
```

**桥引用 S4 即可，不需要新钉法。** R4 起草据此进行。

## 仍然欠着

```
S8 异卷备份    做不到 —— 本机只有 C:。registry 与其全部历史现在同在一块盘上
R4             可以起草了（证伪器未触发）；ratify 之前「禁止追加任何 CR1 行」持续在 force
```
