# REGISTRY_MOVED_NOT_A_REGISTRY

**This file is a tombstone. It is not the trial registry and must never be
read as one — not as an empty registry, not as an unauthorised one.**

The canonical `ops/TRIAL_REGISTRY.md` moved out of this repository under
migration Route A on 2026-08-31. Route A's S5 was ruled `GIT_ONLY`
(`dec-s5-r4-2026-08-27`, adopted by Aaron the same day): a tombstone here and
**no readable copy left behind**. The earlier form the ruling had suggested —
a renamed copy `ops/TRIAL_REGISTRY.pre-migration.<date>.md` — was retired by
that ruling, because such a name matches the non-exact `TRIAL_REGISTRY*`
pattern the conflict-copy detector refuses by construction.

## Where the registry is now

```
REGISTRY_REPO      C:\Users\Aaron\quant-data\itsf-registry
REGISTRY_PATH      ops/TRIAL_REGISTRY.md      (relative path deliberately unchanged)
N0  init commit    378e95c8f6a243630841f9cd212d4f3f6a698b2e
N1  arrival commit e71e54fea3e01244340e4d0364bdbfbc53a1ef23
SHA0               ee9da33fdbb47725dc036243adc76d7d9ba69ff06df0df443b09103f897353d6
BYTES              6697
LINE_COUNT         37
EVENT_COUNT        17
```

The relative path is unchanged on purpose: the approved CR1 syntax block
names `ops/TRIAL_REGISTRY.md` verbatim in `CR1_REGISTRY_INTACT_PREIMAGE` and
in `COLD_RECOMPUTE`, so both sentences stay literally true in the new
repository without being reworded.

## Where the bytes still are, twice over

```
this repository   the blob at O0 = 51fa5192d5b24803a8883a7f3a99318c69e81255
                  `git show 51fa5192:ops/TRIAL_REGISTRY.md`
the new repository the working file and the blob at N1
```

Both were verified byte-identical to SHA0 before this tombstone was written.
`GIT_ONLY` places the rollback on the first of those, which is why C1 —
history bytes == working-tree bytes == SHA0 — had to hold before anything
moved, and did.

## Independent witness, outside both repositories

```
C:\Users\Aaron\quant-data\registry-witness\itsf\WITNESS_S1_2026-08-31.json
sha256 97ab6b732af7dfc3d7295e4413e1aae59d01b71b9064391d3cbff6a6264327b8
```

It records the sha256, the event count and the last line as they stood
before the move, together with the rule by which events were counted — so a
later check cannot pass by counting a different way.

## Outstanding

Invariant 10 requires a bare repository on a different physical volume, or an
offline bundle. **This machine has only C:**, so that obligation is not met
today. It is recorded here rather than left to be discovered: until a second
volume exists, the registry and its history live on one disk.
