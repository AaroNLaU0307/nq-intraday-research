# INCIDENT —— 传输声明钉了 HEAD，然后我把 HEAD 挪了

```
INCIDENT_ID=INC-TRANSPORT-HEADPIN-20260825
DATE=2026-08-25
SEVERITY=一次 Sol 审查会话作废（零裁定产出）
FAULT=builder（Opus 5）。Sol 的行为完全正确。
CLASS=第二次传输失败；与 INC-TRANSPORT-20260824 **机制不同**
```

## 1. 发生了什么

```
STATUS=STOP        RULING=NOT_ISSUED
六份工件字节数与 SHA-256 全部 MATCH，工作树 clean
声明 HEAD  ba9745340b07650a396136c2f9820cc504295ed1
实测 HEAD  f8b8f8bc743573cb5f94748be13b10c4c72b4ab9
```

Sol 按传输规则停下，未分析提案，未发裁定，未改任何文件。

## 2. 我做了什么导致它

1. 写 Sol 提示词，在 `## Transport` 块里印了一行 `HEAD: ba97453…`；
2. **把这份提示词 commit 了** → HEAD 变成 `167045f`；
3. 又 commit 了 Aaron 的四项裁定 → HEAD 变成 `f8b8f8b`；
4. Aaron 把提示词贴给 Sol。

**声明在我 commit 提示词那一刻就已经过期了。** 钉 HEAD 这件事本身是自毁的：
提交提示词就会改 HEAD，所以这个钉子写下去的同时就失效。

## 3. 实质上没有任何东西变了——这不是辩解，是定级依据

```
$ git log ba97453..HEAD -- <送审的六份>
（空）
```

两个 commit（`167045f` 提示词、`f8b8f8b` Aaron 裁定转录）**没有碰送审集的任何
一个字节**。六份对登记表逐一复核，6/6 MATCH。所以 Sol 停在**声明不符**上，
不是实质不符。**但停得对**：Sol 无法在不分析的前提下知道 HEAD 的移动无关，而
「不必信任发送方关于变了什么的说法」正是传输声明存在的全部意义。

## 4. 我的守卫为什么没抓到——这一条最难看

`tests/test_artifacts_under_review_are_frozen.py` 是我在 08-24 那次事故之后
**专门为防这类失败**建的。这次它**全程绿灯**：

- `test_every_artifact_under_review_still_hashes_to_what_was_sent` 比的是
  字节，字节没变，通过。
- `test_no_review_prompt_carries_a_hash_the_register_disagrees_with` 比的是
  提示词里的哈希与登记表，两者一致，通过。

**两条守卫都只覆盖了上一次事故的确切形状**（「我改了复审者手上的工件」），
而不是它所属的类（「我让复审者手上的声明不再描述这棵树」）。这是一个反复出现
的模式：我把上一次的失败编码成守卫，然后被同一类的下一个变种打中。

## 5. 还有一件更值得记的：两个复审席位对同一条规则给出了相反行为

标准传输规则（`~/.claude/CLAUDE.md`）原文只说**工件哈希**：

> 任何送审工件须先以持久文件存在并记录 SHA256，接收方开工前重算并比对；
> 缺失、截断或不符即 STOP 并报告。

规则**没有提 HEAD**。于是：

- **Fable**（08-25 早些时候，同类情形：声明 `13fb936`，实测 `0991d6f`）读作
  「传输规则以字节为准，字节相符，非实质」，**继续并交付了提案**。
- **Sol**（本次）读作声明字段，**STOP**。

两边都讲得通。**歧义在我的提示词排版里**：我把 `HEAD: <sha>` 印在
「重算并比对，不符即 STOP」这句话正下方的 Transport 块内，它看上去就是个待比对
字段。Sol 完全照字面执行。

## 6. 修法

**不是**「以后记得更新 HEAD」——那是意图，不是控制。改钉一个不会过期的性质：

```
REVIEW_ID                    = <登记表里的 review_id>
REVIEWED_SET_UNCHANGED_SINCE = <40-hex>
VERIFY = git log <that>..HEAD -- <送审路径>   ->  必须为空
```

为什么这个比钉 HEAD 好：

- **接收方可自证**，不必相信发送方关于「那两个 commit 无关」的说法；
- **无关工作落地不会使它过期**——这条修复本身就要 commit，而它不碰送审集，
  所以钉子在自己的修复之后依然成立；
- 保留了信号：真有 commit 碰了送审路径，它就该响。

### 落地的三条机械守卫

| 守卫 | 抓什么 | 变异验证 |
|---|---|---|
| `test_the_register_is_well_formed` | 登记项必须带 40-hex `unchanged_since` | — |
| `test_no_commit_has_touched_a_reviewed_path_since_its_declaration` | 声明之后有 commit 碰了送审路径 | **已验**：把某项的钉子回拨到该文件上次改动之前，守卫报出那个 commit |
| `test_a_review_prompt_never_pins_a_bare_head` | 活跃 review 的提示词里出现裸 `HEAD: <40-hex>`，或缺 `REVIEWED_SET_UNCHANGED_SINCE` | **已验**：把停掉 Sol 的那一行原样塞回去，守卫报出 |

### 变异验证过程里的一个自纠，一并记下

第一次做变异证明时，我把 `13fb936` **手工补齐成 40 位**当作 `unchanged_since`
写进去。那个 sha 不存在，`git log` 直接失败，于是「未被抓到」这个结论**什么也
没证明**。第二版改为用 `git rev-parse` 解析真实 commit，并**在跑守卫之前先断言
这个钉子确实被违反**，然后守卫抓到了。

**没有对自身 setup 做断言的变异证明不是证明**——这句话我在 08-24 写过一次，
这次又踩了一次。

## 7. 另一条我不自己改的

活跃 review 期间**任何** commit 都是一次传输事件，即使它不碰送审工件。这次那两个
commit 都是正当工作（提示词本身、Aaron 裁定的转录），但代价真实。可选的收紧是
「review 出门期间不 commit」，但那会把正当工作全堵住。

**规则层的歧义（HEAD 是否属于传输声明）在 `~/.claude/CLAUDE.md` 里，那是 Aaron
的文件，本记录只提出、不修改。** 建议的澄清：明确写「传输声明以工件哈希为准；
若要额外声明仓库状态，用 `REVIEWED_SET_UNCHANGED_SINCE` 而不是 HEAD」。

## 8. 处置

- Sol 提示词已重发：Transport 块改为上述形式，并在其中**直白写明这次 STOP 是
  作者的错以及错在哪**，免得下一个读它的席位重蹈或困惑。
- 登记表六项补 `unchanged_since = ba97453…`（该点之后无 commit 碰过它们，已核）。
- 三条守卫落地，其中两条经变异验证。
- 送审集字节零变动，Sol 可直接重跑开场核对。
