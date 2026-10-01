＃ HOLD 修复记录 · ENG-SAFETY-PRE-REAL-DATA-001

```ini
RECORD_TYPE=REPAIR（不授权、未读真实数据、未签 P2）
BY=Opus 5，builder seat，2026-09-02
BASIS=Aaron「我先出个门，把能做的都做了」
SCOPE=H1 / M1 / H2 —— 三条工程缺陷，均不沾 Aaron 六类保留项
NOT_IN_SCOPE=① 何时读真实数据 · ③ live P2 · archived_bytes_deleted 的终态裁定
```

---

## 0. 每一条都是先复现、再修

**没有一条是照席位描述直接改的。** H1 用真实 `archive_sealed_run` 跑出来，
M1/M2 按构造复现，H2 按构造复现。修之前先写会红的测试。

## 1. H1 —— 链路不绑定 seal 与归档树

```
修前  out_dir / runs_dir / archive_root 三个自由参数
      -> 可以封进一棵树、归档另一棵
      -> 实测 P4 + archive_ok，而 seal 不在归档里，拷进去的是空目录
修后  只收一个 PlannedPaths
      out_dir      = planned.runs_target
      归档         = ARCHIVE_SEAM(out_dir, planned.archive_parent)
```

**绑定规则不是我发明的。** `plan_supplement_paths` 是**已批的规划器**，
它本来就拥有这个关系——`archive_parent` 的注释逐字写着
「**`archive_sealed_run` 必须被传这个**」。从一个对象导出两条路径，
让「解绑」在结构上不可能，而不是靠人记得别解绑。

### 1.1 修 H1 顺带挖出两个缺陷

```
一  C_BUILD_1 的「必须为空」一直在查错的目录
    它查 runs_root，而 seal 写去 out_dir —— 两者不相干时，
    「写之前为空」和「seal 已归档」一样是空话。
    绑定后它真的看见了上一次的 seal，并在写之前停住。

二  那条拒绝以**裸 DayStrataRowsError** 逃出链路
    而其余每一处停止都是具名的 ChainRefusal
    —— 与 H2 报的裸 FileNotFoundError 同形。时刻 1 的生产者拒绝现已具名。
```

### 1.2 一条测试被改写，因为它把缺陷钉成了预期

`test_it_creates_no_directory_of_its_own` 原本断言 P4 之后 `runs` 不存在。
**它通过的原因是错的**：归档拷的是空目录，seal 在别处。
现在改为断言**链路不凭空造出任何调用方没给的目录**。

## 2. M1 —— `retry_permitted` 被当作封存成功

```
修前  run_c_build_2 在非异常路径上无条件 local_seal_ok=True
      而 resolve_partial 会返回 retry_permitted —— 那是「debris 挪开、
      路径解封」，**什么都没封**
      -> 链路先做真实归档 I/O，事后 Router B 才说 nothing was sealed
修后  读 action：{already_sealed, promote} 才算封成
```

**两半都测了**，所以「一律返回 False」蒙混不过去。

## 3. H2 —— 没有 gate-first 的组合路径

```
新增  supplement_chain.run_supplement_gate_first
      A_PRECHECK(13) -> B_DERIVE(5) -> 运行目录 -> C_BUILD 三个时刻
      每一处停止都是具名 ChainRefusal，带 stage 与 gate
```

**为什么建它不会打开执行：** A_PRECHECK 里就有 live-authorization 那几道门，
**今天就会拒绝**。把阶段按序组合起来不会削弱它——只是让拒绝发生在
**本该发出它的第一道门**，而不是从来没被问过。

### 3.1 那个无人拥有的 mkdir，现在有主了

```
refuse_to_create_run_directory   默认姿态：命名该步骤，但不执行
make_run_directory               **必填、无默认** —— 调用方必须说清谁来建
目录没被真的建出来               具名拒绝 run_directory_absent，
                                 不再是裸 FileNotFoundError
```

`DIRECTORY_CREATION_AUTHORIZED=NO` 依然成立，**而且现在是可见的**。

## 4. 生产入口的拒绝理由已订正

它原先说「执行路径已存在（supplement_chain）」——**那个只跑 C_BUILD**。
现在指向 `run_supplement_gate_first`，并说明仍然缺的是 dataset 侧输入
（要读真实数据，且没有任何地方配置 job_dir）。

## 5. 没修的，以及为什么

```
archived_bytes_deleted 的终态   需要在四个后继里裁定，或改已批封闭枚举
                                （R4 级）—— 两者都不是 builder 能做的
M3 的两条                       E: 备份卷不存在 / manifest 优先级
                                —— 是否在 ① 之前恢复副本，归 Aaron
①③                             归 Aaron
```

## 6. 状态

```
测试   4998 -> 见提交（全绿）
执行   仍然 DEFAULT-REFUSE。未读任何真实数据，未建任何 quant-data 目录
```
