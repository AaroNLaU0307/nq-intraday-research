# `$` 锚定的身份校验器 —— 已有守卫只扫了七个，另有五个从没被扫过

```ini
RECORD_TYPE=FINDINGS
DATE=2026-08-29
FOUND_BY=builder（工作会话）
SEVERITY=MEDIUM
STATUS=已修 + 已把清单改为从源码导出
```

## 1. 已有守卫的范围

`tests/test_mc_supplement_paths_battery.py::test_no_anchored_pattern_admits_a_trailing_newline`
早就在扫这一类，它的 docstring 写着 `THE SWEPT CLASS`。

**它扫七个模式，全部在 `itsf.mc.supplement_contract`**，来自一个手写元组，
并有 `assert len(ANCHORED_PATTERNS) == 7` 钉住条数。

## 2. 实测：另外五个从没进过那张表

```
atoms._UPPER_CONST     ^[A-Z][A-Z0-9_]*$
atoms._HEX64           ^[0-9a-f]{64}$
consumer._HEX64_RE     ^[0-9a-f]{64}$
report._DATE_RE        ^\d{4}-\d{2}-\d{2}$
runinfra._HEX64_RE     ^[0-9a-f]{64}$
```

**五个全部接受尾随 `\n`。其中三个校验 SHA-256 摘要。**

Python 里 `$` 匹配「字符串末尾**或**末尾换行之前」；`\Z` 才是末尾。

## 3. 形态，又一次

**一条守卫的范围停在它作者当时所在的那个模块，
而它命名的性质（「没有任何锚定模式接受尾随换行」）是整个仓的性质。**

那条已有守卫**并没有写错**——它钉住了它声明的东西。
**但没有任何东西会在有人新加一个文件时把它变红。**

## 4. 修法：让清单从源码导出，而不是再手列一张

`tests/test_every_identity_pattern_is_swept.py`：

```
导出规则   模块级 re.compile 赋值，模式以 ^ 开头、不含具名分组
           -> 视为「整词校验器」，必须以 \Z 结尾
豁免       行解析器须在 LINE_PARSERS 里逐条声明理由，否则失败
自检       导出到的模式数必须 > 8（扫到零个的守卫会报「干净」）
           已声明的豁免必须仍然存在（陈旧豁免没人会注意到）
```

导出面实际找到 **9 个**：五个身份校验器 ＋ 四个带 `re.S`、作用在 `.strip()` 过的
文本上的行解析器（`mc_registry` / `supplement_registry` 的 `_NOTE_BRACKET_RE`
与 `_FIELD_RE`）。**后四个的 `$` 是「捕获到末尾」，不是身份锚**，已逐条声明豁免
并写明四个调用点。

## 5. 这是生产改动

```
改了   atoms.py · consumer.py · report.py · runinfra.py 各一处 $ -> \Z
性质   收紧，不放宽 —— 之前被接受的只有「带尾随换行的非规范值」
未改   supplement_contract.py（它在 c-build-2-wording-r3 的冻结登记册里，
       且它那七个本来就已经是 \Z）
实测   全量 4506 绿
```

**注意与本周 ITSF 侧其余工作的区别**：那些都是机制零改动（裁定 B 的 CONDITIONS）。
**本次不在 C_BUILD_2 措辞的范围内**，改的是无关模块的正则锚点。
若 Aaron 认为措辞复审期间不该有任何 `src/` 改动，本次可回退 ——
回退代价是那五个身份校验器继续接受尾随换行。

## 6. 姊妹仓同批

`qros-runtime` 的四个身份校验器（`FROZEN_OID` · `_HEX40` · 两个 `_HEX64`）
是同一次排查里量到的，同样已修，记录见
`qros-runtime/build-evidence/BUILDER_FOUND_DOLLAR_ANCHOR_2026-08-29.md`。

**两仓合计九个身份校验器接受尾随换行，其中六个校验 SHA-256 或 git OID。**

---

## 7. 追加：又找到五处，而且**两条守卫都比它们声称的窄，其中一条是我几小时前写的**

### 7.1 `ANCHOR_MODULES` 那条守卫的 docstring 说了假话

`tests/test_mc_supplement_integration.py::test_no_validating_anchor_in_any_supplement_module_uses_dollar`
的 docstring 逐字写着：

> This sweeps every module by **SOURCE**, so a new one joins the check by
> existing rather than by being remembered.

**它迭代的是 `ANCHOR_MODULES`，一个手写的六元组。** 而 `src/itsf/mc/` 有 **21 个模块**。

**更要命的是它的来历**：这条守卫本身就是为了修「上一版守卫只反射它知道的那两个模块」
而写的。**修复重演了它要修的那件事，并在自己的 docstring 里声称没有。**

实测（HEAD~6 的树，即我今晚动手之前）：

```
atoms.py     2 处 ^...$   —— 清单外，这条守卫看不见
consumer.py  2 处 ^...$   —— 清单外，看不见
```

**已改为 glob 目录**，`ANCHOR_MODULES` 只留作下界（其中每个名字必须仍被 glob 到，
否则「glob 悄悄不匹配了」会通过）。变异证红：把 `$` 放回 `atoms.py` → 红；旧版看不见。

### 7.2 我自己那条新守卫，今晚被加宽了两次

```
第一版   只走 tree.body   -> 看不见函数内的 re.compile、看不见容器字面量里的
第二版   走整棵 AST       -> 仍看不见 f-string 模式（ast.Constant 判定不成立）
第三版   处理 JoinedStr   -> 才看全
```

**为「阻止扫描比它声称的性质窄」而写的守卫，自己窄了两次，用了一个晚上。**
本仓三条同类扫描里，**两条有过这个缺陷**。

### 7.3 因此又找到五处

```
consumer.py:1048   函数内 hex64 = re.compile(r"^[0-9a-f]{64}$")   校验 manifest 摘要
runinfra.py:720-723  _SCHEMA_PATTERNS 四条日志 schema 白名单
```

**四条 schema 的严重性要说准**：那是 Stage-C 的**日志泄漏白名单**，
docstring 写着「宁可误杀」。它接受 `message + "\n"` ——
**但 `message + "\nLEAKED SECRET"` 不通过**（`$` 只匹配末尾那一个换行之前）。
**所以没有信息能骑在上面，这是不精确，不是泄漏。**

修的理由不是防泄漏，是：**一个声称「宁可误杀」的白名单，
不该接受一个它没有列出的变体。**

### 7.4 本仓 `$` 锚定的身份校验器现在合计

```
第一批（§2）   atoms._UPPER_CONST · atoms._HEX64 · consumer._HEX64_RE
              report._DATE_RE · runinfra._HEX64_RE            5 处
第二批（§7.3） consumer.py:1048 · runinfra._SCHEMA_PATTERNS ×4  5 处
合计           10 处，加上姊妹仓 4 处 = **14 处**
```

**其中八处校验 SHA-256 或 git OID。**
