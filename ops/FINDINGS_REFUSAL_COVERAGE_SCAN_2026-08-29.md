# 扫描每一条 `raise` 的失败码 —— 以及我第一次扫错了 19 倍

```ini
RECORD_TYPE=FINDINGS
DATE=2026-08-29
FOUND_BY=builder（工作会话）
STATUS=三条已补测试；扫描方法的错误一并记录
```

## 0. 先记我做错的那一步 —— 它比结果重要

扫全部 `src/**/*.py` 的 `raise SomeError("code", ...)`，共 **290** 个失败码。
然后问：**哪些码没有任何测试提到？**

**第一次口径**：测试文本里是否出现**完整码串**。答案：**59 个从未提及**。
按模块分层后 `src/itsf/s0/costs.py` 尤其扎眼 —— **6 个码，6 个全未提及（100%）**，
而它是成本模型。我正要把它写成一条重大发现。

**写之前去看了 `test_costs.py`，第 283 行是：**

```python
with pytest.raises(ValueError, match="duplicate_minute_slot"):
```

`match=` 是 `re.search`。**部分字面量匹配完整码。**
我按完整串查存在性，于是把每一次部分匹配都记成了「未覆盖」。

**改用正则语义重扫**：

```
完整串口径（错）      59 个「从未提及」
子串/正则口径（对）    3 个
costs.py 的六条        **六条全部被匹配**
```

**错了约 19 倍，而且差一点发布出去。**

**这与 §12.5 是同一个形状**：量对了一件事（完整串不存在），
说出了另一件（没被测过）。**抓到它是因为我去开了测试文件，没采信自己的扫描。**

## 1. 三条真的没有任何测试字面量能匹配

```
atom_type_violation      src/itsf/mc/atoms.py:539             atom_canonical_dict
cold_trace_not_text      src/itsf/mc/cold_reducer.py:80       parse_jsonl
gate_not_in_c_build      src/itsf/mc/supplement_contract.py:414  checkpoint_of
```

**三条都不是缺陷**，都是输入校验的拒绝，只是从来没有东西跑过它们。
**一条没被执行过的拒绝，是一条没人见过它工作的拒绝。**

已补 `tests/test_the_three_unreached_refusals.py`（12 条 + 5 subtests），
每条同时测「拒绝成立」与「合法输入仍放行」。

顺带在写「合法输入」时被 `cold_trace_schema` 拒了一次 —— 我造的行缺 `schema` 字段。
**那证明的是 schema 检查有效，不是文本被接受**，已改为从模块常量构造。

## 2. 这次扫描**不**主张什么

```
「有一个字面量可能匹配」 ≠ 「那条 raise 被执行过」
```

一条测试可能匹配了别的码而恰好共享子串。**只有行覆盖能定论。**
本件给出的是**下界**：3 条连能匹配的字面量都没有。

上界要等 `coverage run`（已在跑，本机全量约 6 分钟，加覆盖率更久）。
**结果出来之前，本件不声称覆盖率数字。**

## 3. 可复现

```sh
# 失败码枚举（AST，不是 grep）
python - <<'EOF'
import ast, io, re
from pathlib import Path
codes = {}
for f in sorted(Path("src").rglob("*.py")):
    tree = ast.parse(io.open(f, encoding="utf-8").read())
    for n in ast.walk(tree):
        if isinstance(n, ast.Raise) and isinstance(n.exc, ast.Call):
            for a in n.exc.args:
                if isinstance(a, ast.Constant) and isinstance(a.value, str) \
                   and re.fullmatch(r"[a-z][a-z0-9_]{4,}", a.value):
                    codes.setdefault(a.value, (f.as_posix(), n.lineno))
print(len(codes))
EOF
```

**判「是否被提到」时必须用子串双向包含**，不是完整串相等 —— 这就是本件的教训。
