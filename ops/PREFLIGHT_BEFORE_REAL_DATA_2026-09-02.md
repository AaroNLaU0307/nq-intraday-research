＃ PREFLIGHT —— 真实 Development 数据之前的最终边界

```ini
RECORD_TYPE=PREFLIGHT（不授权、不执行、未读任何 Development 数据）
BY=Opus 5，builder seat，2026-09-02
MEASURED_AT=bbae823edc782cf999120cb8441bf3bafae4304f
# 不写 HEAD=：提交这份记录本身就会移动 HEAD，写下的那一刻即为陈旧。
# 这正是冻结登记册表头记着的那条（2026-08-25 有一个 Sol 会话为此 STOP）。
# ③ 必须绑定**签署当时**的 HEAD，不是这里的任何一个值。
按 Aaron 2026-09-02 的七项要求逐条回答
```

---

## 0. 先更正我先前告诉你的一句话（安全相关）

检查点 4 §5 我写：

> 「构造它们要读 S0 数据集，是 Development 数据读，**被门挡着**。」

**执行之后，这句话是错的。**

```
assert_real_run_allowed(G9_FLAG, SECOND_COPY_FLAG)   -> 通过
  gate1/G9_RESOLVED.flag           存在（2026-08-25）
  ops/SECOND_COPY_ATTESTED.flag    存在（2026-08-25）
```

**那道门今天是开的。** 我把「有一道门」错说成了「那道门会拒绝」。

真正拦住真实读取的是**另外两件事**，两件都不是那道门：

```
一  run_supplement_production 在 P2 检查处拒绝
    "0 live SUPPLEMENT_EXECUTION_AUTHORIZED row(s) — exactly one is required"
二  **整个代码库里没有任何地方配置了 job_dir**
    DevelopmentSignalLoader 要求调用方提供它；没有任何常量、配置或默认值
```

**推论，必须说清楚：** 直接用一个 job_dir 调 `DevelopmentSignalLoader.load_real`
**不会被那道门拦住**。保护来自「补充路径上没有任何代码调用它」和
「没有目录可指」，**不是**来自守卫会拒绝。

---

## 1. 最终工程状态与测试结果

```
HEAD      bbae823edc782cf999120cb8441bf3bafae4304f
测试      4997 passed, 473 subtests passed（全绿，无跳过失败）
冻结哈希  verify_frozen_hashes 通过
冻结登记册 ops/ARTIFACTS_UNDER_REVIEW.json  under_review = 0
```

本阶段新建/改动（全部无需真实数据）：

```
supplement_precheck.py   A_PRECHECK 13 道装配与逐道报告
supplement_derive.py     B_DERIVE   5 道
supplement_build.py      C_BUILD    5 道
day_strata_pipeline.py   ＋ run_c_build_2 / SealStagingResult；_declared_digest 修复
supplement_chain.py      三个时刻的编排器
supplement_inputs.py     bars -> universe/flag/ruled methods（最后一层）
supplement_contract.py   ＋ gates_at / CHECKPOINT_ORDER
supplement_runner.py     C_BUILD_2 门接线；decide_after_seal ＋ post_archive_ok
day_strata_classify.py   封存码四桶（BD-6）
```

## 2. 下一步读取 Development 数据具体会读什么、产生什么副作用

**唯一的真实读取点：`itsf.data.dbn_loader.DevelopmentSignalLoader.load_real`。**

```
读什么
  <job_dir>/manifest.json  或  <job_dir>/_local_manifest.json     清单
  <job_dir>/<filename>                                            DBN 数据文件
  —— 且仅此两者。没有目录遍历，没有第二个根

顺序（冻结的失败关闭次序）
  1  assert_real_run_allowed        今天通过（见 §0）
  2  _check_role                    job_dir 路径必须含 development_signal，
                                    且不得同时含其他 role 标记
  3  verify_file_against_manifest   逐字节 sha256 对清单
  4  _decode -> _postprocess        纯内存

副作用
  dbn_loader 内**没有任何写入调用**（AST 实测：write/mkdir/unlink/replace 全无）
  -> 读取本身不产生副作用
```

**读之后，链路下游才产生副作用**，且都在你指定的根之下：

```
build_universe / encode_f10 / 取已裁定方法    纯，无副作用
run_c_build                                   纯（只做快照对拍）
run_c_build_2 -> seal_supplement_production
  写 <output_root>/.../supplement.json.partial 然后提升为 supplement.json
archive_sealed_run
  写 <archive_root>/<run-dir>.partial 然后 os.replace 提升
  **从不修改 runs_dir 的任何字节**
```

## 3. production chain 是否已从真实数据入口一直可达至预期封存/失败状态

**必须分成两半回答，因为你要的这项措辞若照字面验证，就得读真实数据 ——
那正是 ① 禁止的。**

```
已执行（可复现）
  合成 1 分钟 bars -> build_universe -> encode_f10 -> 已裁定 vol/event 方法
  -> 真实 rows -> 三道 C_BUILD_1 门 -> **真实生产封存器** -> resolve_partial
  -> Router B -> **P4**
  除归档 I/O 一步用桩外，全程不打桩
  测试：test_bars_to_P4_with_NOTHING_mocked_but_the_archive

  失败侧同样已执行：
    C_BUILD_1 拒绝    停在写之前，目录里什么都没有
    seal 冲突         停在时刻 2（真路径：封一次、改字节、再封）
    本地 seal 消失    Router B「nothing was sealed」
    归档字节被删      A1（BD-5）
    Router B seal 码  拒绝，且门从未被问过
    归档失败报告      A1，不是 P4

从未执行
  load_real 一次都没有跑过
  真实 bars 从未进入过这条链路
  run_supplement_production 本身仍在 P2 检查处拒绝，从未越过
```

**所以诚实的说法是：从 bars 起的每一步都已组合并跑通到预期终态；
而「从真实入口」这一段，我不能声称已验证 —— 它需要 ①。**

## 4. 尚存的 blocker / residual

```
BLOCKER
  B1  没有 job_dir。代码库里没有任何地方命名 Development 数据目录         -> ①
  B2  没有 live P2。run_supplement_production 在此拒绝                     -> ③

RESIDUAL（不阻塞，但要一起进下一次 review）
  R1  第 8 轮之后那次 resolve_partial 修复，从未被独立席位看过。
      本阶段把 C_BUILD_2 接线并接进能跑到 P4 的链路，**承重增加了两层**
  R2  UNMAPPED_SEAL_CODES 7 条 —— 全部大声拒绝，但都还没有门
      （BD-6；其中 3 条是「builder 的答案是否适用于封存路径」）
  R3  UNMAPPED_BUILDER_CODES 机制仍在，表为空
  R4  P2 契约字段名与解析器字段名的历史不一致（见 §7，已按解析器为准）
  R5  S8 跨卷备份仍未满足（只有一个卷）—— 迁移时即已记录
```

**按你 2026-09-02 的安排，R1/R2 不单独开轮，搭下一个自然 review 节点，
且该 review 只审工程安全与实现边界、不读 outcome-carrying 内容。**
禁读清单由 `ops/OUTCOME_CARRYING_ARTIFACTS.json` 机器生成，随包附上。

## 5. 当前完整 40 位 HEAD

```
测量时     bbae823edc782cf999120cb8441bf3bafae4304f
本记录提交后  见 git（提交这份文件必然再次移动 HEAD）
```

**这里不钉一个「当前 HEAD」，因为写下的那一刻它就过期了** ——
提交这份 preflight 本身就移动 HEAD。冻结登记册表头为同一原因记着
「HEAD itself is NEVER pinned」，2026-08-25 有一个 Sol 会话正为此 STOP 过。

**③ 必须绑定签署当时的 HEAD。** 我会在你要签之前，用 `git rev-parse HEAD`
当场报给你，并确认工作树干净。

## 6. ① 的精确授权需求

**① 要给的不是一句「可以读了」，而是三样具体的东西**，否则代码无处可指：

```
①-a  逐字的 job_dir 绝对路径
     必须包含 development_signal，且不得同时包含其他 role 标记
     例：C:\...\development_signal\<JOB>
①-b  要读的文件名（一个或多个）与 source_format（默认 "dbn"）
①-c  确认该目录下存在 manifest.json 或 _local_manifest.json，
     且待读文件的 sha256 已在其中
```

以及一句明确的授权语，形如：

> 授权在 `<①-a 逐字路径>` 读取 `<①-b 文件名>`。这是本次授权的封闭清单，
> 仅此目录与仅此文件，不含通配符。我知道这会触及真实 Development 数据。

**我不会代你拟这句话的内容**；上面是形状，路径与文件名由你给。

**① 之后我仍不会跑任何真实读取** —— ① 只解开「把 job_dir 接进代码」，
真正执行仍需 ③，且届时我会先把接线做完、跑完全量、把 HEAD 稳定下来再来找你。

## 7. ① 完成后才可使用的 P2 精确授权需求

**以解析器为准（契约文档里的字段名与解析器不一致，历史遗留，见 R4）：**

```
事件         SUPPLEMENT_EXECUTION_AUTHORIZED
actor        必须是 Aaron（不是我，也不是任何模型）
note 必须以这个 token 开头
             START_MC_DS_S001_DAY_STRATA_SUPPLEMENT_EXECUTION
note 字段    ";" 分隔的 "key: value"，三个键缺一不可
             supplement_id:    MC-DS-S001
             authorized_commit: <完整 40 位十六进制>
             output_root:       <绝对路径>
额外硬约束   登记行的 commit 单元格**必须等于**句子里的 authorized_commit
             （不一致时失败关闭，不挑赢家）
```

**顺序，这一条是上次出错的地方：**

```
①  先给 job_dir           -> 我接线、跑全量、HEAD 稳定
③  再签 P2，绑定那个稳定的 HEAD
```

上次我把 P2 说成最后一道门，而入口当时是 `-> NoReturn`，
于是你签了一条按其自身「HEAD 移动即失效」条款**永远无法被行使**的授权
（`ops/P2_WITHDRAWN_NO_EXECUTION_PATH_2026-08-31.md`）。**不再重复那个顺序。**

---

## 8. 我在本阶段被守卫拦下三次，都记在这里

```
一  seal 侧继承 builder 的答案
    -> test_the_SEAL_side_still_refuses_the_same_code 当场拒绝，且它是对的
       freeze_payload 冻结整个 payload 含 binding，两条路径含义不同
       结果：三个共用 raise 点我一个都没拿，全记为 UNMAPPED
二  用 iter_day_contexts 取事件 flag
    -> test_no_module_in_the_package_reaches_a_forbidden_name 拒绝
       该路径通向标签计算，而补充是 structural-only
       结果：改用 events.encode_f10，同值、无 bars、无 contexts
三  裁定编号 BD-2 / BD-3 与 2026-08-29 记录冲突
    -> 已改为 BD-5 / BD-6
```

**外加 §0 那条自我更正：一道我以为会拒绝的门，实际是开的。**
