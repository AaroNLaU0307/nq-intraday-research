＃ N04 执行路径 · 检查点 1 —— 十八道门的实测位置

```ini
RECORD_TYPE=MEASUREMENT（不授权、不执行、不读 Development 数据）
BY=Opus 5，builder seat，2026-08-31
SCOPE=A_PRECHECK（13 道）＋ B_DERIVE（5 道）
NOT_IN_SCOPE=C_BUILD（5 道）—— 下一个检查点
```

---

## 0. 为什么有这份记录

昨天我告诉 Aaron 剩余距离是三步，**错了**，而正确答案当时就写在入口函数的
签名里（`-> NoReturn`）。所以这一段改成**分段交付**：每段结束时给出
**测出来的**位置，而不是我说的位置。

**这是第一段。**

---

## 1. 结果

```
A_PRECHECK   13 道
  8 PASS
  5 REFUSE   live_authorization_unique · authorization_actor ·
             authorized_commit_matches_head · output_root_declared ·
             output_root_structure
             —— 五道全部只等一样东西：一条 live 的 P2

B_DERIVE      5 道（对**生产形态**输入实测，不是合成夹具）
  4 PASS      custody_authority_production · source_bundle_digest ·
              day_universe_identity · method_version_pinned
  1 REFUSE    custody_authority_binding
              "authority commit 876c1b74131b != HEAD f5ca3801f628"
              —— 夹具把 authority 钉在历史 S0-T001 的 commit 上（测试文件第 55 行的常量），
                 而门要求它等于当前 HEAD。**门是对的，夹具是旧的。**
                 真跑时该值由 P2 携带
```

**十八道门里没有一道因为「代码没建好」而拒绝。**
全部要么通过，要么在等 P2 带来的那个 commit。

**`custody_authority_production` 通过这件事本身证明输入是生产形态的** ——
那道门按设计拒绝 TEST_ONLY，所以它不可能被合成夹具骗过。

## 2. 建了什么

```
src/itsf/mc/supplement_precheck.py   装配真实 A_PRECHECK 上下文并逐道报告
src/itsf/mc/supplement_derive.py     装配 B_DERIVE 上下文并逐道报告
tests/test_supplement_precheck.py    13 条
tests/test_supplement_derive.py       8 条
```

**两个模块都不改任何拒绝行为。** 两个生产入口的 `NoReturn` 与其消息一字未动，
两个新模块都不被它们调用。

### 2.1 一个刻意的设计：**装配接收，从不生产**

`supplement_derive` 把 `prepared` 作为**参数**，永不创建它。
理由是量出来的，不是设计出来的：

```
derive_supplement_authority(prepared)   给定 prepared 即为纯函数
                                        （其 docstring：without any repository read）
prepare_real_mc_input()                 唯一触及真实数据者，且已被
                                        authorize_real_mc 挡住（今天必抛）
```

所以**装配可以被测、被审，而唯一会花掉东西的那一步仍在原有的门后面**。

该声称被证了三遍，而不是被声明：

```
按源码   AST 里不得出现 prepare_real_mc_input / prepare_mc_input /
         authorize_real_mc，也不得 import real_input
按签名   两个公开函数的 `prepared` 都不得有默认值
         —— 有默认值就等于留了一个绕过口，而声称仍读起来为真
按行为   跑一遍，治理目录逐字节不变
```

**第二条是写的时候才想到的。**

### 2.2 为什么是「报告」而不是「运行」

`run_stage_gates` 首拒即停 —— 对运行是对的，对回答「还差多远」是无用的。
**「第一道拒绝的门」和「十三道里哪几道会拒绝」是两个不同的问题。**

## 3. 过程中的三个错，都是「静默匹配不到」

```
一  从记忆打函数名 assert_frozen_hashes（真名 verify_）
    -> AttributeError 被吞进 gap -> 字段留 None -> 门失败关闭
    -> **我差点报成「有冻结文件被改动」**。七条哈希手算全 OK 才拦住
二  测试声称「这是真测量」，而断言只查值∈(True,False) —— 假设也满足
    -> 变异（改成假设）没打中 -> 去查为什么，才发现断言比声称窄
    -> 补了能分辨的两条：让 guard 报 tamper，要求装配器把它带到门
三  夹具重新导出按 `_pytestfixturefunction` 匹配，pytest 9 已不再设置它
    -> 循环一个都没匹配到，**且不报错**
    -> 改为按类型匹配，并断言结果里必须含所需的两个夹具
```

**三个都是同一形状：一个匹配不到任何东西的检查，和一个匹配到正确东西的检查，
长得一模一样。**

## 4. 下一个检查点

```
C_BUILD 5 道   全部经由 _classify_c_build_1，读 ctx.c_build_outcome
               「缺席即拒绝」：没有 outcome 时放行，等于对一次从未发生的构建
               记下「未发现缺陷」
待建           装配层接收 c_build_outcome（由 run_c_build 产出），逐道报告
               —— 同样是装配与执行分开
```

**到那时，「还差多远」会是一张 23 道门的完整实测表。**
