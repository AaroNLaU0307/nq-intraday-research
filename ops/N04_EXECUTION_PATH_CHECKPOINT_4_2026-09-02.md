＃ N04 执行路径 · 检查点 4 —— 链路跑通到 P4，剩下的缺口不在路径上

```ini
RECORD_TYPE=MEASUREMENT（不授权、不执行、不读 Development 数据）
BY=Opus 5，builder seat，2026-09-02
SCOPE=编排器（三个时刻）＋ gates_at ＋ 一个集成缺陷 ＋ 一个欠你的裁定
BASE=94ae805（检查点 3）
```

---

## 0. 一句话结论

**三个时刻的链路已组合完成，并在真实封存器 + 真实临时目录上跑到 `P4`。**

`run_supplement_production` 那句「this build carries no execution path」
**今天起为假，已订正**。

而真正的剩余缺口**不在执行路径上**：链路要接收 `universe / vol_method /
flag_by_date`，构造它们要读 S0 数据集 —— 那是 Development 数据读，
被函数顶部的 `assert_real_run_allowed` 挡着。

**缺口是「被门挡住的数据获取」，不是「缺路径」。**

---

## 1. 建了什么

```
src/itsf/mc/supplement_contract.py   ＋ gates_at(checkpoint) ＋ CHECKPOINT_ORDER
src/itsf/mc/supplement_chain.py      三个时刻的编排器
src/itsf/mc/day_strata_pipeline.py   _declared_digest 修复（见 §3）
src/itsf/mc/supplement_runner.py     订正那句已为假的拒绝理由
tests/test_supplement_chain.py       14 条
tests/test_day_strata_pipeline.py    ＋ 4 条（那条缺失的覆盖）
```

### 1.1 按时刻取门，而不是按 stage

```
时刻 1  row_schema_blind · day_set_exact · rows_digest_recompute   写之前
时刻 2  seal_staging_partial                                       暂存中
时刻 3  archive_policy_a                                           —— 不经门，走 Router B
```

`gates_at` 的分区被断言为**精确**：3+1+1=5，无重复、无遗漏、顺序取自 `GATE_TABLE`。
未知 checkpoint **抛异常而不是返回空元组**——空元组会跑零道门，
**和一个合法地没有门的时刻长得一模一样**。

结构断言两半都做了：链路源码里不得出现 `run_stage_gates`（AST），
**并且**证明那道门确实会拦住它——否则「避开它」只是风格，不是承重。

## 2. 一个**故意不填**的缺口，欠你一条裁定

`run_c_build_3` 会报 `archived_bytes_deleted`：**本地 seal 活着，但先前已归档的字节没了。**

```
Policy A     P4 需要 local_seal_ok AND archive_ok  -> 不能是 P4
Router B     只能经 classify_archive_report 到达 A1
             而对 status=archive_ok 的报告，它抛 archive_ok_has_no_code
archive_sealed_run  只校验它自己刚做的那份拷贝，不看更早归档的字节
```

**于是报告可以说 ok，而检查点说归档毁了证据——没有任何既有裁定覆盖这一对。**

我没有替你选。链路**具名拒绝**，并在拒绝文本里写明这需要你的裁定。
`local_seal_absent / local_seal_mutated` 两个码不需要裁定——它们就是
`local_seal_ok=False`，Router B 早有答案。

**选 A1 会把一个终态悄悄发给一个没人裁定过的情形。**

## 3. 组合暴露出的一个真实集成缺陷

```
_declared_digest(product)   docstring：「however it carries it」
实际                        只认顶层 dict 与 .rows_digest 属性
真实 SupplementProduct      字段在 .payload 里
-> 一个完全正常的产品，第一次组合链路时以
   product_carries_no_rows_digest 被拒
```

**又一句比实现宽的声称，而它活下来的原因是覆盖缺口:**
这个仓所有测试都用一个顶层 dict 的合成产品驱动它。

修法是补上 payload 这一支，**并把每个取值器旁边写明「什么东西会构造这个形状」**——
以及补一条用**真工厂**构造产品的测试，这样字段搬家会在那里红，
而不是在一条链路的末端红。

## 4. 链路测到哪

```
干净链路              -> P4，真封存、真文件、rows 数等于已封存日集
归档失败报告          -> A1（Policy A：本地成功 + 归档失败 ≠ P4）
C_BUILD_1 拒绝        -> 停在时刻 1，且**目录里什么都没有**（写之前）
Router B 的 seal 码   -> 拒绝，且**门从未被问过**（把门换成会炸的桩来证）
seal 冲突             -> 停在时刻 2，走真路径
本地 seal 消失        -> local_seal_ok=False -> Router B「nothing was sealed」
归档字节被删          -> 具名拒绝（§2 的缺口）
自身不建任何目录      -> runs / archive 都不存在
```

## 5. 现在还差什么

```
①  链路的 dataset 侧输入（universe / vol_method / flag_by_date）
    —— 要读 S0 数据集，是 Development 数据读，已被门挡住
       这不是「缺代码」，是「缺授权」，且不该由我从这里打开
②  §2 那条欠你的裁定（archived_bytes_deleted 的终态）
③  一条 live 的 P2 —— 仍然只有你能签，且仍应在 ① 之后
```

**②③ 归你。① 归你决定何时动真实数据。**

## 6. 一条仍然站着的残留

`ops/DELIVERY_C_BUILD_2_WORDING_AT_CAP_2026-08-30.md` §0：
**第 8 轮之后那次修复，从未被任何独立席位看过。**

检查点 3 让执行路径开始依赖它；本检查点把它接进了一条能跑到 `P4` 的链路。
**承重又增加了一层。** 这条我仍然不替你判定。
