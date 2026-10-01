# ATTESTATION HEADER — copy verbatim to the top of every verifier attestation

```
ATTESTATION_VERSION=2 (QROS-CF v2; ops/REVIEWER_CONTRACT.md §4)
VERIFICATION_SCOPE=<as in the brief>
OBLIGATION=RUN_IDENTITY | STAGE_I | BOTH
BLINDNESS_REQUIRED=CLAIM_BLIND | OUTCOME_BLIND
BLINDNESS_ACHIEVED=CLAIM_BLIND | OUTCOME_BLIND | NONE
FRAMEWORK_COMMIT=<40-hex>
VERIFIER_MODEL=<model id>
VERIFIER_SESSION=<fresh top-level session id, date>
NOT_THE_PRODUCER=YES | NO
NOT_A_PRIOR_SEAT_FOR_THIS_FAMILY=YES | NO
EXPOSURE_BEFORE_FREEZE=NO | YES(<what>)
DEVELOPMENT_DATA_READ=NO | YES(<why authorized>)
GIT_COMMANDS_RUN=NONE | <list>
MODULES_EXECUTED_NOT_INSPECTED=<list>
FROZEN_RESULT=<relative path> sha256 <64-hex> frozen_at <ISO>
ALLOWLIST_RECOMPUTED=MATCH | MISMATCH(<paths>)
FORMAL_VERDICT=PASS | PASS_WITH_BACKLOG | HOLD | <family row: VERIFIED | FAILED(<code>)>
NEXT_LEGAL_REGISTRY_EVENT=<token or NONE>
REGISTRY_APPENDED=NO
INDEPENDENCE_PER_DIMENSION=context:<fresh session> authorship:<non-author> model_diversity:<family vs producer> empirical:<n/a for identity; sample statement for Stage I>
```

The sha256 of the attestation file itself is recorded by the dispatcher in the registry row / ops/DECISIONS.md; the file cannot contain its own hash.
