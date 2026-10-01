# R2_FORWARD_PIT_COLLECTION

```
RECORD_TYPE = DATA_COLLECTION_INFRASTRUCTURE
LINEAGE     = R2
CREATED     = 2026-09-20
UPDATED     = 2026-09-21 (two-defect model: MSA principal CLOSED; cmd quoting
              repair built, awaiting one local credential step)
STATUS      = BUILT · TESTED · FIRST CAPTURE TAKEN · RECURRING SCHEDULE INSTALLED
              LOGON REPAIR PENDING ONE LOCAL CREDENTIAL STEP (see §6)
MICROSOFT_ACCOUNT_PRINCIPAL_MODE = YES
MICROSOFT_ACCOUNT_EMAIL          = NOT_PERSISTED
PASSWORD_REGISTRATION_DEFECT     = MICROSOFT_ACCOUNT_PRINCIPAL_RESOLUTION -> CLOSED
TASK_ACTION_EXECUTION_DEFECT     = CMD_EXE_OUTER_QUOTING
CMD_QUOTING_DEFECT               = CONFIRMED; repair built, re-registration pending
FORWARD_TASK_LOGON_TYPE          = PASSWORD (live)   PRINCIPAL_IS_MSA_FORM = YES
FIRST_NATURAL_SCHEDULED_RUN      = OBSERVED_FAIL_2026_09_21 (see §6c)
NEXT_NATURAL_SCHEDULED_RUN       = 2026-09-22 11:00 Asia/Kuala_Lumpur
FORWARD_COLLECTION_AUTONOMY = INTERACTIVE_ONLY
RUN_WHILE_USER_LOGGED_OUT   = NO
S4U_UPGRADE_FOR_FORWARD_COLLECTOR = FORBIDDEN_WRONG_FIT
COLLECTOR   = v1.1.0, manifest schema v2

FORWARD_COLLECTION_DOES_NOT_REPAIR_2010_2021 = YES
POST_2022_SAMPLE_TIER_REMAINS_UNASSIGNED     = YES
```

**Evidence taxonomy.** A snapshot taken here is
**`DIRECT_CONTEMPORANEOUS_PIT_CAPTURE_EVIDENCE`** — an observation of the public endpoint
made at the time of observation. Its integrity rests on the **immutable-snapshot
convention**, the **manifest**, the **SHA-256 digests**, and the **preserved raw bytes and
raw headers**. The filesystem read-only attribute applied to snapshot files is an
**operational safeguard only** and must never be described as cryptographic immutability.

---

## 1. Purpose

Capture the public ProShares/ProFunds per-fund historical NAV files for the five R2
universe funds as **immutable, dated, hashed snapshots**, preserving raw bytes, raw HTTP
response headers and both client retrieval timestamps.

The reason this exists is the single most decision-relevant finding of SV-1: **the
2010-2021 problem is a retention problem, not a data problem.** The one vendor class that
keeps genuine ETF fund-size vintages keeps roughly five years of them, because the need it
serves is operational rather than historical. Deep vintage archives are not sold because
nobody kept them. The only way to hold a deep vintage archive later is to start one now.

Each snapshot answers, for a **future** date, the question `R2_G3_HISTORICAL_PIT_AMENDMENT`
could only answer partially for the past: *what did the endpoint actually serve, and when
did we see it?* — producing **`DIRECT_CONTEMPORANEOUS_PIT_CAPTURE_EVIDENCE`**: an
observation made at the time, rather than an inference drawn from an archive afterwards.

## 2. What this is NOT — the non-repair limitation

This collection does **not**:

- repair 2010-2021 — it collects forward dates only and creates no historical evidence;
- assign a post-2022 sample tier — `POST_2022_SAMPLE_TIER = UNASSIGNED`, unchanged;
- authorize a Development-window extension — `R2_SAMPLE_EXTENSION_DECISION = DEFERRED`;
- authorize Validation or Lockbox use of any date;
- authorize S1 — `R2_S1_AUTHORIZED = NO`;
- consume a trial — `TRIAL_CONSUMED = NO`;
- constitute a research observation, a measurement, or any claim.

```
SAMPLE TIER OF EVERY DATE COLLECTED HERE = UNASSIGNED
```

Assigning one is an Owner decision and nothing in this file anticipates it. A snapshot is
evidence that a value was available at a time. It is not permission to use that value.

## 3. Relationship to OD-5 and OD-6

- **OD-5 (`PATH_A_TRUE_PIT_DAILY`)** requires a daily fund-size representation with true
  historical point-in-time availability evidence. This collector manufactures exactly that
  evidence, prospectively.
- **OD-6 (`PROVEN_PUBLICATION_ONLY_ZERO_CARRY`)** makes a date ineligible unless
  availability is *proven*. A snapshot taken at time `T` showing a row for `t-1` is a
  proof of availability by `T` for that row. Snapshots that show a row **absent** are
  equally valuable — rule 8 (a row published too late does not enter date `t`) and rule 9
  (a later backfill does not retroactively make date `t` eligible) can only be applied to
  a future date if the absence was observed at the time. **That is why the collector
  records failures rather than skipping them.**
- Backlog item **G-10** (no guarantee the URL pattern, directory index or header semantics
  persist) is addressed directly: every capture snapshots, hashes and records headers, and
  a schema change is flagged rather than absorbed.
- Blocker **G-11** (the batch can miss a trading day, observed 2016-04-01) becomes
  detectable going forward: a stalled batch shows up as an unchanged `Last-Modified`, an
  unchanged `latest_row_date`, or a lagging fund — all recorded per snapshot.

## 4. Collection schema

**Endpoint** (already audited, `R2_DATA_SOURCE_AUDIT` B-1 and its 2026-09-19 amendment):

```
https://accounts.profunds.com/etfdata/ByFund/{TICKER}-historical_nav.csv
TICKER in {PSQ, QID, QLD, SQQQ, TQQQ}        (OD-2 universe, sorted)
```

**Directory layout** — immutable, one directory per snapshot, never overwritten:

```
data_forward_pit/
  YYYY-MM-DD/                       (America/New_York date)
    HHMMSS_ET/                      (America/New_York time)
      PSQ/  PSQ-historical_nav.csv          raw response bytes
            PSQ-http-response-headers.txt   raw status line + headers
            PSQ-error.txt                   only if transport failed
      QID/  QLD/  SQQQ/  TQQQ/      same
      MANIFEST.json                 deterministic, sorted keys, schema v2
      MANIFEST.sha256               sha256 of every file, sorted by path
```

**Per-fund manifest record** — the fourteen required facts, plus what makes them checkable:

| # | requirement | manifest field |
|---|---|---|
| 1 | raw response bytes | `body_path`, `body_bytes` |
| 2 | raw HTTP response headers | `headers_path` |
| 3 | client retrieval timestamp, UTC | `retrieved_utc` |
| 4 | client retrieval timestamp, America/New_York | `retrieved_et` |
| 5 | HTTP `Date` | `http_date` (+ `http_date_utc`, `http_date_et`) |
| 6 | `Last-Modified` | `last_modified` (+ `last_modified_utc`, `last_modified_et`) |
| 7 | `ETag` | `etag` |
| 8 | `Content-Length` | `content_length` (+ `content_length_matches_body`) |
| 9 | latest row date | `latest_row_date` (+ `oldest_row_date`) |
| 10 | row count | `data_row_count` |
| 11 | SHA-256 of raw file | `body_sha256` |
| 12 | SHA-256 of headers | `headers_sha256` |
| 13 | request URL | `url` |
| 14 | HTTP status | `http_status` |

Also recorded per fund: `status` · `attempts[]` (every attempt, so an original failure is
never hidden by a retry) · `transport_error` · `columns` · `column_count` ·
`parse_status` · `unparsable_row_count` · `missing_headers[]` · `notes[]`.

Snapshot-level: `schema_monitor` (compared against the previous snapshot) and `summary`
(`funds_ok`, `funds_failed`, `latest_row_date_max`, `lagging_funds`,
`funds_with_missing_headers`, `funds_with_parse_problems`).

**Failures are recorded, never swallowed.** A 404, a timeout, a missing header, a lagging
fund, malformed CSV and a schema change each produce an explicit record and a non-zero
exit. The whole value of the archive is that it preserves staleness evidence.

**Schema monitoring.** Column names, column count, latest date and row count are recorded
every time. If columns differ from the previous snapshot, `schema_change = YES` and both
versions are preserved side by side. **No research calculation is ever adapted
automatically** — the collector flags and stops flagging is all it does.

## 5. First capture — identity and hashes

```
SNAPSHOT_ID  = 2026-09-19/125150_ET
DIRECTORY    = data_forward_pit/2026-09-19/125150_ET
CAPTURE_TYPE = INFRASTRUCTURE_VALIDATION        (NOT a research observation)
STARTED_UTC  = 2026-09-19T16:51:50.216887Z
STARTED_ET   = 2026-09-19T12:51:50.216887-04:00
FUNDS_OK     = 5/5      SCHEMA_CHANGE = NO_BASELINE      LAGGING_FUNDS = none
VERIFY       = PASS
MANIFEST_SHA256 = 2a549931663af7a14b970a754b07ddf2a10fe8b289e2b25341cc660e9e32ac00
```

| fund | HTTP | bytes | rows | oldest row | latest row | `Last-Modified` (ET) | ETag | body sha256 (first 16) |
|---|---|---|---|---|---|---|---|---|
| PSQ  | 200 | 414,968 | 5,095 | 2006-06-19 | 2026-09-18 | 2026-09-18 21:01:06 | `"654f8-65bcb8d3add4b"` | `d27ffbfa88b0bee3` |
| QID  | 200 | 454,971 | 5,080 | 2006-07-11 | 2026-09-18 | 2026-09-18 21:00:56 | `"6f13b-65bcb8caaf0e7"` | `2a2339d614797a04` |
| QLD  | 200 | 455,921 | 5,095 | 2006-06-19 | 2026-09-18 | 2026-09-18 21:01:02 | `"6f4f1-65bcb8d084500"` | `6f567db402587d0b` |
| SQQQ | 200 | 405,549 | 4,178 | 2010-02-09 | 2026-09-18 | 2026-09-18 21:01:12 | `"6302d-65bcb8d94b4e1"` | `a7cf5bbf21859afd` |
| TQQQ | 200 | 409,104 | 4,178 | 2010-02-09 | 2026-09-18 | 2026-09-18 21:01:01 | `"63e10-65bcb8cf5bdb5"` | `7905de6556cdacf8` |

Nine-column schema intact and identical across all five funds:
`Date · ProShares Name · Ticker · NAV · Prior NAV · NAV Change (%) · NAV Change ($) ·
Shares Outstanding (000) · Assets Under Management`.

`Content-Length` equals the received body length for all five.

**Three independent corroborations fell out of this capture, and none was engineered:**

1. **Origin clock agreement.** The server's own `Date` header (`Sat, 19 Sep 2026 16:51:51
   GMT`) matches the client's recorded retrieval instant to **1.17-1.47 s** across the five
   funds — round-trip plus offset. Both timestamps are recorded on every capture precisely
   so that client-clock error can never silently corrupt availability evidence.
2. **Byte-identity with an independent earlier capture.** All five bodies are
   **byte-identical** to `data_probe/g3_timing_2026-09-19/`, taken about 3 h 46 min earlier
   by a different tool. Append-only behaviour held over that interval — consistent with,
   and independent of, the G-6 result recorded in `R2_DATA_SOURCE_AUDIT` A-5.
3. **Launch dates reproduce.** Oldest rows are PSQ/QLD 2006-06-19, QID 2006-07-11,
   SQQQ/TQQQ 2010-02-09 — matching `R2_FEASIBILITY_REPORT` §3.1 exactly.

Evening batch times (21:00:56-21:01:12 ET on the row's own date) sit inside the pattern
already recorded in `R2_G3_PUBLICATION_TIMING_REPORT.md`. **This is noted as continuity of
the artifact, not as a new timing claim**, and one capture extends nothing.

### A note on the snapshot's date

The snapshot id derives from the client clock, which reads 2026-09-19 in ET. The origin
server's `Date` header independently agrees. The session harness reports 2026-09-20. Where
the two disagree, the snapshot is named from the clock that the origin corroborates, and
both timestamps are preserved in the manifest so the question is always re-answerable from
the artifact rather than from memory.

## 6. Recurring schedule — installed

```
FORWARD_TASK_NAME      = QuantTrade-R2-ForwardPIT
FORWARD_TASK_INSTALLED = YES        FORWARD_TASK_ENABLED = YES (State: Ready)
SCHEDULE               = Daily, every CALENDAR day, DaysInterval = 1
LOCAL_TIME             = 11:00
TIMEZONE               = Asia/Kuala_Lumpur (machine TZ is UTC+08:00, no DST;
                         trigger StartBoundary 2026-09-20T11:00:00+08:00)
FIRST_SCHEDULED_RUN    = 2026-09-20 11:00 +08:00
INTERPRETER            = C:\Users\Aaron\AppData\Local\Programs\Python\Python314\python.exe
                         (Python 3.14.2)
LOGON_TYPE             = Password (live) under MicrosoftAccount\<redacted-account-email>
ACTION_ARGUMENTS       = OLD /c form still stored <-- pending re-registration
RUN_WHILE_USER_LOGGED_OUT = YES by configuration (LogonType Password); the action
                         must still be re-registered before a run can succeed
START_WHEN_AVAILABLE   = true
MULTIPLE_INSTANCES     = IgnoreNew
EXECUTION_TIME_LIMIT   = PT1H
BATTERY                = AllowStartIfOnBatteries, DontStopIfGoingOnBatteries
WAKE_TO_RUN            = not enabled (no system power setting was modified)
DUPLICATE_TASKS        = 0
EXPORTED_DEFINITION    = ops/R2_FORWARD_PIT_TASK.xml
```

### Why 11:00 Malaysia time, every calendar day

11:00 in Kuala Lumpur is **23:00 ET on the prior US calendar day during EDT** and
**22:00 ET during EST**. Both are after the ~21:00 ET evening batch recorded in
`R2_G3_PUBLICATION_TIMING_REPORT.md`.

**This does not guarantee the batch has completed, and no such guarantee is claimed.** A
late, stale or missing update is **evidence, not a failure of the scheduling design** —
capturing exactly those days is the point. The time is fixed deliberately and is **not
tuned from observed fund behaviour**: the object is the public state at a reproducible
clock time, not the best state.

It runs **every calendar day**, with no market-calendar dependency used to decide whether
to run. A weekend or holiday capture showing unchanged data is useful contemporaneous
state evidence. The manifest records `trading_day_status` as **WEEKEND** when the US
Eastern date is Saturday or Sunday and **UNKNOWN** otherwise — a weekday may still be a
market holiday, and `TRADING_DAY` is never asserted, because asserting it would require a
market calendar this collector deliberately does not depend on.

### Logon model — corrected 2026-09-21 (Microsoft Account principal)

```
S4U_UPGRADE_FOR_FORWARD_COLLECTOR = FORBIDDEN_WRONG_FIT
S4U_USED = NO        S4U_UPGRADE_RECOMMENDED = NO
MICROSOFT_ACCOUNT_PRINCIPAL_MODE = YES
MICROSOFT_ACCOUNT_PASSWORD_VALIDATED_EXTERNALLY = YES
MICROSOFT_ACCOUNT_EMAIL = NOT_PERSISTED
```

**S4U stays withdrawn.** It issues a logon token carrying **no network credentials**, and
this collector exists to make outbound HTTPS requests. Wrong fit, not merely unavailable.

#### Root cause of the earlier registration failure

It was **not a wrong password**. Aaron validated the credential externally with
`runas` using his Microsoft Account password and a new session opened, so the password and
the account principal are both good.

The defect was **principal resolution**. Two different things were being conflated:

| | value on this machine | what it authenticates |
|---|---|---|
| **local profile identity** | `DESKTOP-B7VTGF0\Aaron` (NTAccount form) | an **interactive token** — fine for `LogonType Interactive` |
| **password auth principal** | `MicrosoftAccount\<account email>` | the **account password** — required for `LogonType Password` |

`Get-LocalUser -Name Aaron` reports `PrincipalSource = MicrosoftAccount` and SID
`S-1-5-21-…-1001`, whose NTAccount translation is `DESKTOP-B7VTGF0\Aaron`. The installer
had been passing that NTAccount form to a password-backed registration, which cannot
authenticate a Microsoft Account password. Hence the failure.

#### The empirical confirmation — a real scheduled run failed

The `InteractiveToken` registration has now **demonstrably failed a natural scheduled
firing**, which is stronger evidence than the theoretical argument:

```
LastRunTime        = 2026-09-21 11:00:01   (the trigger fired)
LastTaskResult     = 1
NumberOfMissedRuns = 0
stdout log entry   = NONE
scheduler JSONL    = NO new record
snapshot created   = NONE
```

`logs/forward_pit_task_stdout.log` has **no line at all** for that firing — the cmd wrapper
never reached its first `echo`, so the action never launched. The identical action string
succeeds when started manually with an interactive session present. The leading explanation
is therefore that no interactive session existed at 11:00, which is exactly what
`LogonType Interactive` cannot survive.

Stated with its limit: the Task Scheduler *Operational* event channel holds no events on
this machine, so the specific launch error code was not recoverable. What is certain is
that the trigger fired, the action produced nothing, and **a day of forward collection was
lost** — `FIRST_NATURAL_SCHEDULED_RUN = OBSERVED_FAIL`.

That day is **`MISSING_FORWARD_CAPTURE`**. It is not backfilled, and no snapshot was
fabricated for it.

#### Current state, stated exactly

```
FORWARD_TASK_LOGON_TYPE           = INTERACTIVE_TOKEN   (repair not yet applied)
FORWARD_COLLECTION_AUTONOMY       = INTERACTIVE_ONLY
AUTONOMOUS_WHILE_USER_LOGGED_IN   = YES
UNATTENDED_WHILE_LOGGED_OUT       = NO
RUN_WHILE_USER_LOGGED_OUT         = NO
MANUAL_SECURE_CREDENTIAL_STEP_REQUIRED = YES
```

The word **autonomous is never used unqualified.**

### The one step Aaron must run himself

The installer is repaired and preflights clean, but registration needs two values that only
Aaron can supply locally — his Microsoft account **email** and the **account password**.
Neither may be typed into a chat, and this automation host cannot prompt securely, so the
step is deliberately left manual. Run in an ordinary local PowerShell window:

```bash
powershell -ExecutionPolicy Bypass -File "C:/Users/Aaron/OneDrive/Desktop/Quant trade/nq-letf-rebalancing-research/tools/install_forward_pit_task.ps1"
```

It will, in order: detect `PrincipalSource = MicrosoftAccount` and enter
`MICROSOFT_ACCOUNT_PRINCIPAL_MODE`; prompt for the account email (shown as typed — it is
not a secret); prompt for the password with `Read-Host -AsSecureString` (never echoed);
register `MicrosoftAccount\<email>` with `LogonType Password` and `RunLevel Limited`;
verify the logon type really is `Password`; re-export and secret-scan the task XML; then
start the task once to exercise the real principal's network and filesystem access.

Before running it:

- A **Windows Hello PIN will not work** — it must be the account password, the same one
  that worked with `runas`.
- If registration fails, the installer **fails closed**: no fallback to
  `DESKTOP-B7VTGF0\Aaron`, no fallback to `InteractiveToken`, and the existing registration
  is left alone. Verified — with no credential available it exits non-zero and leaves the
  task byte-identical.
- The validation run is labelled `UNATTENDED_SCHEDULER_VALIDATION` via a one-shot marker
  that the wrapper consumes and deletes, so routine collections are never mislabelled.

Afterwards, confirm at any time without exposing the email:

```bash
powershell -ExecutionPolicy Bypass -File "C:/Users/Aaron/OneDrive/Desktop/Quant trade/nq-letf-rebalancing-research/tools/install_forward_pit_task.ps1" -Mode VERIFY
```

On success the state becomes:

```
FORWARD_TASK_LOGON_TYPE     = PASSWORD
RUN_WHILE_USER_LOGGED_OUT   = YES
FORWARD_COLLECTION_AUTONOMY = PASSWORD_BACKED_UNATTENDED
MANUAL_SECURE_CREDENTIAL_STEP_REQUIRED = NO
```

### What a validation run does and does not prove

Starting the registered task exercises the real principal: its network access, its
filesystem access and the whole wrapper chain. It does **not** prove that Windows will wake
and fire the task at a future wall-clock time — and the 2026-09-21 failure shows that
distinction is not academic.

**True logged-out validation will not be attempted.** Proving it would mean logging Aaron
out of Windows and disrupting his session, so `TRUE_NO_INTERACTIVE_SESSION_VALIDATED = NO`
and stays `NO`. The password-backed logon type is itself sufficient to *configure*
`RUN_WHILE_USER_LOGGED_OUT = YES`; the destructive real-world observation remains untested
by choice.

### Credential safety

The account email is prompted locally, used only to build the principal string in memory,
and **not persisted** — `MICROSOFT_ACCOUNT_EMAIL = NOT_PERSISTED`. Every principal printed
by the installer or written to these records is redacted to
`MicrosoftAccount\<redacted-account-email>`.

The password is read as a `SecureString`, marshalled to plaintext **only inside** the
`Register-ScheduledTask` call, with the unmanaged buffer zeroed in a `finally` block. It is
passed as a cmdlet parameter, never on a command line, so it cannot reach shell history or
a process listing. It is never written to the repository, task XML, `.ps1`, `.cmd`, logs,
`PROJECT_STATE`, documentation, environment files, stdout or stderr. Windows stores it as an
**LSA secret**, not in the task XML; the installer scans the export anyway and deletes it
rather than keep anything suspicious.

### OneDrive / user-profile check

The project lives under `C:\Users\Aaron\OneDrive\Desktop\Quant trade\...`. Every required
file is checked for OneDrive Files-On-Demand placeholder attributes (`OFFLINE`,
`RECALL_ON_OPEN`, `RECALL_ON_DATA_ACCESS`) and zero length: **all are fully local**, and
`tools/`, `data_forward_pit/` and `logs/` are plain directories. The task needs only the
existing local files and **does not require the OneDrive sync client to be running**. The
installer repeats this check on every run and refuses to register if a required file is an
online-only placeholder — reporting the blocker rather than moving the project.

### Commands

Install or re-install the schedule:

```bash
powershell -ExecutionPolicy Bypass -File "C:/Users/Aaron/OneDrive/Desktop/Quant trade/nq-letf-rebalancing-research/tools/install_forward_pit_task.ps1"
```

Remove the schedule (removes only `QuantTrade-R2-ForwardPIT`; snapshots and logs untouched):

```bash
powershell -ExecutionPolicy Bypass -File "C:/Users/Aaron/OneDrive/Desktop/Quant trade/nq-letf-rebalancing-research/tools/remove_forward_pit_task.ps1"
```

Collect once manually, outside the schedule:

```bash
python "C:/Users/Aaron/OneDrive/Desktop/Quant trade/nq-letf-rebalancing-research/tools/collect_forward_pit.py"
```

Verify any snapshot (re-derives every hash, checks the manifest against the files, checks timezones):

```bash
python "C:/Users/Aaron/OneDrive/Desktop/Quant trade/nq-letf-rebalancing-research/tools/collect_forward_pit.py" --verify data_forward_pit/2026-09-19/125150_ET
```

Run the full test suite:

```bash
python -m unittest discover -s tools -p "test_*.py" -v
```

Check the schedule's state and last result:

```bash
powershell -Command "Get-ScheduledTask -TaskName QuantTrade-R2-ForwardPIT; Get-ScheduledTaskInfo -TaskName QuantTrade-R2-ForwardPIT"
```

### Logs

```
logs/forward_pit_scheduler.jsonl      append-only operational log, one JSON object per run
logs/forward_pit_task_stdout.log      captured stdout + stderr of every scheduled invocation
logs/forward_pit_console.log          wrapper console transcript
logs/.forward_pit.lock                single-instance lock (present only while running)
```

Each JSONL record carries `invocation_id`, `scheduled_time`, `actual_start_time`,
`late_by_seconds`, `collector_exit_code`, `snapshot_id`, `manifest_sha256`,
`error_summary`, `host_timezone`, `collector_version`, `python_executable`,
`trading_day_status`, and operational counts (`funds_ok`, `funds_failed`,
`schema_change`, `lagging_fund_count`).

**The scheduler log carries no fund values and no research calculation** — a dedicated
test asserts this. Fund-level detail lives only in the snapshot manifests.

## 6a. Failure, missed-run and concurrency semantics

**Exit codes** (propagated unchanged, so Task Scheduler's Last Run Result is truthful):

| code | meaning |
|---|---|
| `0` | all five funds captured and the snapshot self-verifies — **or** a correct `SKIPPED_ALREADY_RUNNING`, which is not a failure |
| `1` | at least one fund failed, or verification failed. **The snapshot is still written** — the failure is the evidence |
| `2` | refused: that snapshot id already exists. A past snapshot is never mutated |
| `4` | collector fault; the traceback is recorded in the JSONL log |

**Statuses:** `COMPLETED` · `COMPLETED_WITH_FUND_FAILURES` · `SKIPPED_ALREADY_RUNNING` ·
`REFUSED_SNAPSHOT_EXISTS` · `COLLECTOR_ERROR`. Nothing fails silently.

**Missed runs.** If the machine is off or asleep at 11:00, `StartWhenAvailable` lets Task
Scheduler run the task when it next can. The collector then records the **real** retrieval
time. A late run is **never presented as having occurred at the scheduled time** — the
JSONL carries `scheduled_time`, `actual_start_time` and `late_by_seconds` separately, and
the manifest carries an `invocation` block with `scheduled_time_local` alongside
`actual_start_local`.

**No catch-up fabrication.** A day with no capture is **`MISSING_FORWARD_CAPTURE`**. No
snapshot is ever reconstructed, backfilled or synthesised for a missed date. The absence is
itself accurate evidence, and inventing one would destroy exactly the property this archive
exists to provide.

**Single-instance safety.** Two guards, deliberately layered: Task Scheduler's
`MultipleInstances = IgnoreNew`, and the wrapper's own lock at `logs/.forward_pit.lock`
(holding pid, host and acquisition time). If a live holder exists, the run records
`SKIPPED_ALREADY_RUNNING` and writes nothing. A lock left by a dead process, or older than
six hours, is treated as stale and cleared, so a crash can never block collection
permanently. The lock is released in a `finally` path even when the collector raises.

## 6b. Scheduler validation capture

One manual run through the identical chain the scheduler uses
(`cmd.exe` → `run_forward_pit_task.cmd` → Python 3.14.2 → wrapper → collector):

```
SNAPSHOT_ID     = 2026-09-19/131606_ET
CAPTURE_TYPE    = SCHEDULER_VALIDATION     (NOT research evidence, NOT routine collection)
INVOCATION_ID   = bf8ee2d266974238
STATUS          = COMPLETED    EXIT = 0    FUNDS_OK = 5/5    VERIFY = PASS
SCHEDULED_TIME  = 2026-09-19T11:00:00+08:00
ACTUAL_START    = 2026-09-20T01:16:06.128470+08:00
LATE_BY_SECONDS = 51366.128        (recorded honestly; this was a manual off-hours run)
TRADING_DAY_STATUS = WEEKEND       (2026-09-19 is a Saturday in US Eastern)
MANIFEST_SHA256 = 631d606e4d95d40ec203c782633337d5af15ba92f632a118c456dcbd9c124e24
```

The first capture, `2026-09-19/125150_ET`, was **not** overwritten: its manifest SHA-256 is
still `2a549931663af7a14b970a754b07ddf2a10fe8b289e2b25341cc660e9e32ac00`, and it re-verifies
`PASS`.

## 6c. The two independent defects (2026-09-21)

Two separate faults were conflated in the earlier record. They are now split, because
each has its own proof and its own fix.

```
PASSWORD_REGISTRATION_DEFECT = MICROSOFT_ACCOUNT_PRINCIPAL_RESOLUTION   -> CLOSED
TASK_ACTION_EXECUTION_DEFECT = CMD_EXE_OUTER_QUOTING                    -> repair built,
                                                                           awaiting one
                                                                           local credential step
```

### Defect 1 — Microsoft Account principal resolution (CLOSED)

The installer authenticated as `DESKTOP-B7VTGF0\Aaron`. `Get-LocalUser` reports
`PrincipalSource = MicrosoftAccount`, and that NTAccount form authenticates an
**interactive token**, not the Microsoft Account **password**. The correct credential
principal is `MicrosoftAccount\<account email>`.

**Status: repaired and confirmed live.** The task is now registered
`LogonType = Password`, principal in MSA form, `RunLevel = Limited`, duplicates 0.

### Defect 2 — cmd.exe outer quoting (CONFIRMED, repair built)

The action was stored as `/c "<script>" "<python>"`. Because the project path contains a
space, cmd.exe strips the quotes and breaks the command at that space.

Reproduced independently here, using a throwaway probe script at a path containing spaces
so the collection archive stayed untouched:

```
A (old form)  cmd.exe /c "<...\Quant trade probe\tools\probe.cmd>" "<python.exe>"
              'C:\Users\...\scratchpad\Quant' is not recognized as an internal or
              external command,
              EXITCODE = 1

B (new form)  cmd.exe /d /s /c ""<...\Quant trade probe\tools\probe.cmd>" "<python.exe>""
              PROBE_OK arg1=C:\Users\Aaron\AppData\Local\Programs\Python\Python314\python.exe
              EXITCODE = 0
```

`/s` plus a **doubled** outer quote pair makes cmd.exe strip only the outermost pair and
take the remainder verbatim. `/d` additionally skips AutoRun, so a machine-local AutoRun
registry value cannot inject itself into an unattended run.

### Correcting the 2026-09-21 11:00 failure attribution

The earlier report attributed that failed natural run to the principal mismatch. **That
attribution is withdrawn as unproven.**

What the evidence actually supports:

- the **principal mismatch** is proven to have broken **password registration**;
- the **quoting defect** is proven to break **action execution**;
- the 11:00 firing produced `LastTaskResult = 1` with **no stdout line, no log record and
  no snapshot** — the signature of an action that never launched, which is the quoting
  defect's signature.

The quoting defect is therefore the better-supported explanation for that specific
failure. It is **not claimed** that either defect alone caused every earlier failed
invocation: at 11:00 on 2026-09-21 the task was registered `Interactive` *and* carried the
broken action, so both faults were present simultaneously and the evidence does not
separate their contributions on that firing. The Task Scheduler Operational event channel
is empty on this machine, so no further discrimination is available.

`FIRST_NATURAL_SCHEDULED_RUN = OBSERVED_FAIL_2026_09_21` stands as a historical fact, and
that day remains `MISSING_FORWARD_CAPTURE` — not backfilled.

### What is left to do

`Set-ScheduledTask` cannot rewrite the action of a password-backed task without the
credential; attempted here, it failed with *"The user name or password is incorrect"* and
correctly **changed nothing** (principal, logon type, run level and the old arguments all
intact). The working credential association was deliberately not gambled to save a step.

One local command completes the repair — it re-registers with the corrected action,
verifies the **stored** arguments are canonical, and then starts the task to validate:

```bash
powershell -ExecutionPolicy Bypass -File "C:/Users/Aaron/OneDrive/Desktop/Quant trade/nq-letf-rebalancing-research/tools/install_forward_pit_task.ps1"
```

Confirm afterwards without exposing the account email:

```bash
powershell -ExecutionPolicy Bypass -File "C:/Users/Aaron/OneDrive/Desktop/Quant trade/nq-letf-rebalancing-research/tools/install_forward_pit_task.ps1" -Mode VERIFY
```

### How this defect is prevented from returning

`tools/task_action.py` is now the **single source of truth** for the argument string. The
installer calls it rather than re-deriving the quoting, validates the result before
registering, and then validates what Windows actually **stored** — a stored action that
lost its outer quoting fails silently with no output, so it is checked rather than assumed.

`tools/test_task_action.py` holds nine regression tests, including two **negative
controls**: one asserting the validator rejects the exact old string that shipped, and one
running real cmd.exe to prove the old form genuinely fails on a spaced path. A ninth test
reads the **live registered task** and asserts its stored arguments are canonical — it is a
standing guard, and it fails today precisely because the live action has not yet been
re-registered.

## 6d. Capture ledger — origin classification

Snapshot manifests are immutable and are **not modified**. Origin is recorded here.

| snapshot | capture_type in manifest | ORIGIN | natural scheduled? |
|---|---|---|---|
| `2026-09-19/125150_ET` | `INFRASTRUCTURE_VALIDATION` | `MANUAL_COLLECTOR_VALIDATION` | NO |
| `2026-09-19/131606_ET` | `SCHEDULER_VALIDATION` | `MANUAL_WRAPPER_CHAIN_VALIDATION` | NO |
| `2026-09-21/063831_ET` | `ROUTINE_FORWARD_COLLECTION` | **`MANUAL_MSA_CONTEXT_DIAGNOSTIC`** | NO |
| `2026-09-21/063916_ET` | `ROUTINE_FORWARD_COLLECTION` | **`MANUAL_MSA_CONTEXT_DIAGNOSTIC`** | NO |
| `2026-09-21/064554_ET` | `ROUTINE_FORWARD_COLLECTION` | **`MANUAL_MSA_CONTEXT_DIAGNOSTIC`** | NO |

**Note on count.** The controller brief named two diagnostic captures; there are **three**.
`2026-09-21/064554_ET` (invocation `55ce8500970c40b6`, 18:45:54 +08:00, 5/5 funds, verified,
exit 0) was created in the same diagnostic session and is classified identically.

All three carry `capture_type = ROUTINE_FORWARD_COLLECTION` in their manifests because they
were produced by direct invocations of the wrapper, which defaults to that label. **They are
valid contemporaneous captures and their bytes are sound**, but they were **not** natural
scheduled invocations and must never be represented as `NATURAL_SCHEDULED_CAPTURE`. The
manifest label records how the wrapper was invoked; this ledger records why.

```
NATURAL_SCHEDULED_CAPTURES_TO_DATE = 0
FIRST_NATURAL_SCHEDULED_RUN        = OBSERVED_FAIL_2026_09_21
NEXT_NATURAL_SCHEDULED_RUN         = 2026-09-22 11:00 Asia/Kuala_Lumpur
```

## 7. What future evidence this creates

For every date collected from here on, the archive will support statements the 2010-2021
record cannot support:

- **that a row for date `t-1` existed at a recorded instant** — an OD-6 availability proof,
  as `DIRECT_CONTEMPORANEOUS_PIT_CAPTURE_EVIDENCE`, with the raw bytes and headers
  behind it;
- **that a row did not yet exist at a recorded instant** — which is what makes OD-6 rules 8
  and 9 applicable at all, and which no retrospective source can reconstruct;
- **a contemporaneous record of any repeat of the 2016-04-01 stall**, per-fund;
- **restatement detection** — successive snapshots of the same rows are directly
  comparable by hash, so a silent historical revision becomes visible instead of
  undetectable;
- **endpoint and schema drift** (G-10), with both versions preserved;
- **per-fund desynchronisation**, via `lagging_funds`.

None of this is a claim about R2's hypothesis, and none of it is usable until a date's
sample tier is assigned by the Owner.

## 8. Implementation and validation

```
tools/collect_forward_pit.py          collector + verifier   (v1.1.0, manifest schema v2)
tools/run_forward_pit_scheduled.py    scheduled wrapper: lock, JSONL log, honest timing
tools/run_forward_pit_task.cmd        Task Scheduler entry point; captures stdout + stderr
tools/install_forward_pit_task.ps1    resolves the interpreter, registers, verifies, exports
tools/remove_forward_pit_task.ps1     removes ONLY QuantTrade-R2-ForwardPIT
ops/R2_FORWARD_PIT_TASK.xml           LIVE export (currently pre-repair Interactive)
ops/R2_FORWARD_PIT_TASK.template.xml  sanitized declarative target, no secrets
tools/test_collect_forward_pit.py     15 tests
tools/test_run_forward_pit_scheduled.py  12 tests
```

Design rules, each chosen for an evidentiary reason: fail loudly · no silent retry · atomic
writes (`.tmp` + `os.replace`) · deterministic manifest (sorted keys, sorted funds) ·
timezone-aware throughout (`zoneinfo`) · SHA-256 everywhere · idempotent with respect to a
snapshot id (an existing id is **refused**, never overwritten) · past snapshots never
mutated · no NQ dependency · no credentials · public HTTP only.

### Three environment problems found and fixed while installing the schedule

1. **The collector depended on `requests`, and the only interpreter carrying it was a
   Windows Store app-execution alias** — a zero-length reparse point, which is not a
   dependable target for an unattended task. The transport was rewritten on
   `urllib.request` (standard library), so the collector now runs under any interpreter
   and needs no third-party package. An HTTP error response is still captured in full,
   because `HTTPError` is itself a readable response object.
2. **The genuine interpreter had no IANA time-zone database.** Windows ships none, so
   `ZoneInfo("America/New_York")` raised `ZoneInfoNotFoundError` under Python 3.14.
   `tzdata` (a pure-data package, 347 KB) was installed into that interpreter and EST/EDT
   conversion verified in both directions. Hand-rolling US DST rules was rejected outright:
   that is precisely the kind of shortcut that silently corrupts timestamp evidence.
   The installer now refuses any interpreter that cannot construct that zone.
3. **The wrapper tests were silently hitting the live endpoint.** `collect()` bound its
   `fetcher` as a default argument, so a patched transport was ignored and the two
   injected-fetcher tests failed while the rest ran against the real network (93 s per
   suite run). The fetcher is now resolved at call time. The suite runs fully offline in
   ~1.6 s, and both previously failing tests pass for the right reason.

### Test results: 27 passed, 0 failed, fully offline

Collector (15): happy path with all fourteen required facts · HTTP 404 preserved with its
body · timeout recorded as a transport error · missing `Last-Modified` flagged without
failing the capture · missing `ETag` flagged · one lagging fund detected · malformed CSV
recorded with raw bytes intact · schema change detected across two snapshots with both
preserved · duplicate snapshot id refused and the prior snapshot proven unchanged
byte-for-byte · re-run at a new time leaves earlier hashes identical · `--verify` detects
tampering · DST-correct timezone conversion · retries record every attempt · manifest
deterministic and sorted · no NQ or research artifact produced.

Scheduled wrapper (12): required log fields present · log contains no fund values · log is
append-only across invocations · a second invocation is skipped while a live lock is held,
writing nothing and leaving the holder's lock alone · a stale lock from a dead process is
broken · the lock is released even when the collector raises · a fund failure produces a
non-zero exit and still keeps the snapshot · a late run is recorded at its real time, never
at the scheduled one · `most_recent_scheduled` rolls back a day before the hour · no
catch-up snapshot is ever fabricated · the manifest records schedule and trading-day status
· `TRADING_DAY` is never asserted.

The suite passes under both the original 3.13 interpreter and the 3.14 interpreter the
scheduled task uses.

### Snapshot verification

Both captures verify `PASS`: every hash reproduces, every manifest path resolves, both
timestamps parse, are timezone-aware and denote the same instant, and the ET offset is
correct for the date. Snapshot files are additionally marked read-only on disk — an
**operational safeguard only**, not cryptographic immutability. Integrity rests on the
immutable-snapshot convention, the manifest, the SHA-256 digests, and the preserved raw
bytes and raw headers.

## 2026-10-01 — scheduled-run evidence to date

Appended at checkpoint CP-R2-V2-01. Earlier sections are **not edited**; where they state
the task's logon type, the pending quoting repair, `NATURAL_SCHEDULED_CAPTURES_TO_DATE = 0`
or `NEXT_NATURAL_SCHEDULED_RUN = 2026-09-22`, this section supersedes them. Every number
below is derived by `tools/reproduce.py` from `logs/forward_pit_scheduler.jsonl`,
`logs/forward_pit_task_stdout.log`, the snapshot manifests and `ops/R2_FORWARD_PIT_TASK.xml`
(REPRODUCED), counted as of snapshot `2026-09-30/144521_ET`.

### Live task, read-only (`Get-ScheduledTask` / `Get-ScheduledTaskInfo`, 2026-10-01 03:35 +08:00)

```
TASK                = QuantTrade-R2-ForwardPIT
PRINCIPAL_LOGON     = Password          RUN_LEVEL = Limited        STATE = Ready
ACTION              = cmd.exe /d /s /c ""...\tools\run_forward_pit_task.cmd" "...\python.exe""
                      (canonical quoting — the §6c repair is applied live)
TRIGGER             = daily 11:00 +08:00, StartBoundary 2026-09-21T11:00:00+08:00
START_WHEN_AVAILABLE= true   MULTIPLE_INSTANCES = IgnoreNew   EXECUTION_TIME_LIMIT = PT1H
LAST_RUN_TIME       = 2026-10-01 02:45:20 +08:00      LAST_TASK_RESULT = 0
NEXT_RUN_TIME       = 2026-10-01 11:00:00 +08:00      NUMBER_OF_MISSED_RUNS = 0
COLLECTOR_VERSION   = 1.1.0 in every JSONL row; manifest schema 2 in every snapshot
                      except 2026-09-19/125150_ET (schema 1, taken before v1.1.0)
```

The live export `ops/R2_FORWARD_PIT_TASK.xml` was re-written at 2026-09-21T19:00:42.16
+08:00 (file time) and the task started 90 ms later: the installer's re-registration and its
`Start-ScheduledTask` validation. The export is no longer "pre-repair Interactive".

### Origin rule (delegate decision D-R2-2026-10-01-02)

A `==== task start` block is written by `tools/run_forward_pit_task.cmd` on **every**
invocation of the `.cmd`, whether Task Scheduler or a person launches it, so the block alone
does not separate scheduled from manual runs (14 captures have a block, 1 has none — an
informational count only). The adopted rule:

```
NATURAL = task-start block present AND capture_type = ROUTINE_FORWARD_COLLECTION
          AND scheduled_time >= trigger StartBoundary (2026-09-21T11:00+08:00)
          AND the only recorded invocation for its scheduled slot
MANUAL  = every other snapshot
CATCH-UP (StartWhenAvailable) = NATURAL with late_by_seconds > 300
```

### Capture ledger

| slot (+08:00) | snapshot | late_by_s | status | funds_ok | verified | capture_type (manifest) | origin |
|---|---|---:|---|---|---|---|---|
| — (no log row) | `2026-09-19/125150_ET` | — | — | 5/5 | PASS | INFRASTRUCTURE_VALIDATION | MANUAL — direct collector run |
| 2026-09-19 11:00 | `2026-09-19/131606_ET` | 51366.1 | COMPLETED | 5/5 | true | SCHEDULER_VALIDATION | MANUAL — wrapper chain validation |
| 2026-09-21 11:00 | `2026-09-21/063831_ET` | 27511.6 | COMPLETED | 5/5 | true | ROUTINE_FORWARD_COLLECTION | MANUAL — MSA context diagnostic |
| 2026-09-21 11:00 | `2026-09-21/063916_ET` | 27556.9 | COMPLETED | 5/5 | true | ROUTINE_FORWARD_COLLECTION | MANUAL — MSA context diagnostic |
| 2026-09-21 11:00 | `2026-09-21/064554_ET` | 27954.7 | COMPLETED | 5/5 | true | ROUTINE_FORWARD_COLLECTION | MANUAL — MSA context diagnostic |
| 2026-09-21 11:00 | `2026-09-21/070042_ET` | 28842.4 | COMPLETED | 5/5 | true | ROUTINE_FORWARD_COLLECTION | MANUAL — installer `Start-ScheduledTask` validation (task context) |
| 2026-09-22 11:00 | `2026-09-21/230004_ET` | 4.6 | COMPLETED | 5/5 | true | ROUTINE_FORWARD_COLLECTION | NATURAL |
| 2026-09-23 11:00 | `2026-09-22/230004_ET` | 4.2 | COMPLETED | 5/5 | true | ROUTINE_FORWARD_COLLECTION | NATURAL |
| 2026-09-24 11:00 | `2026-09-23/230004_ET` | 4.3 | COMPLETED | 5/5 | true | ROUTINE_FORWARD_COLLECTION | NATURAL |
| 2026-09-25 11:00 | `2026-09-24/230004_ET` | 4.4 | COMPLETED | 5/5 | true | ROUTINE_FORWARD_COLLECTION | NATURAL |
| 2026-09-26 11:00 | `2026-09-25/230005_ET` | 5.0 | COMPLETED | 5/5 | true | ROUTINE_FORWARD_COLLECTION | NATURAL |
| 2026-09-27 11:00 | `2026-09-27/020143_ET` | 10903.8 | COMPLETED | 5/5 | true | ROUTINE_FORWARD_COLLECTION | NATURAL — catch-up, fired 14:01:40 |
| 2026-09-28 11:00 | `2026-09-27/230001_ET` | 1.5 | COMPLETED | 5/5 | true | ROUTINE_FORWARD_COLLECTION | NATURAL |
| 2026-09-29 11:00 | `2026-09-28/230001_ET` | 1.5 | COMPLETED | 5/5 | true | ROUTINE_FORWARD_COLLECTION | NATURAL |
| 2026-09-30 11:00 | `2026-09-30/144521_ET` | 56721.5 | COMPLETED | 5/5 | true | ROUTINE_FORWARD_COLLECTION | NATURAL — catch-up, fired 2026-10-01 02:45:20 |

```
SNAPSHOTS = 15 · JSONL_ROWS = 14 · NATURAL = 9 (2 catch-ups) · MANUAL = 6 · VERIFIED = 15/15
```

Catch-ups are recorded at their **real** time: both show the true `actual_start_time` and
`late_by_seconds`, and neither is presented as an 11:00 capture. The 2026-09-20 slot has no
firing record in the logs; it predates the current trigger's StartBoundary.

**Missing day.** The 2026-09-21 11:00:01 trigger firing produced `LastTaskResult = 1`, no
stdout line, no JSONL row and no snapshot (§6c). That slot is **`MISSING_FORWARD_CAPTURE`**
and is not backfilled: the four later 2026-09-21 invocations are manual and do not stand in
for it.

**The three 2026-09-21 manual captures labelled `ROUTINE_FORWARD_COLLECTION`**
(`063831_ET`, `063916_ET`, `064554_ET`) carry that label in their immutable manifests
because the wrapper was invoked directly and defaults to it; the manifests are not modified.
They must never be represented as natural scheduled captures. `070042_ET` carries the same
label for a different reason: the installer's one-shot `UNATTENDED_SCHEDULER_VALIDATION`
marker was written with a UTF-8 BOM (Windows PowerShell 5.1 `Set-Content -Encoding utf8`),
the wrapper's `json.loads` rejected it, deleted it and fell back to the default label. Its
manifest is likewise not relabelled. Backlog row **BL-R2-01** (see `DECISION_LOG.md`).

### What this shows and does not show

It shows that the password-backed task **fires and captures unattended**: nine consecutive
daily slots 2026-09-22 … 2026-09-30, each `COMPLETED` with 5/5 funds and a self-verifying
snapshot, two of them via StartWhenAvailable after the machine was unavailable at 11:00.

It does **not** repair 2010-2021 point-in-time availability, it assigns **no** post-2022
sample tier (`POST_2022_SAMPLE_TIER = UNASSIGNED`), it does not show that the task runs with
no user logged on (`TRUE_NO_INTERACTIVE_SESSION_VALIDATED = NO`, unchanged), and no capture
here is a research observation.

### Corrections to the §8 table

`tools/collect_forward_pit.py` is v1.1.0 (manifest schema 2). `ops/R2_FORWARD_PIT_TASK.xml`
is the live password-backed export with the canonical `/d /s /c` action, not "pre-repair
Interactive". The test suite now has 40 tests plus 12 subtests (the number is printed by
`tools/reproduce.py`, which is its source).

## Correction of record 2026-10-02 — CP-AUDIT-01 (R2-G10, side observations i and iii)

Appended under delegate decision D-R2-2026-10-02-01 (`DECISION_LOG.md`); findings in
`audits/2026-10-01_CP-AUDIT-01/2026-10-01_CP-AUDIT-01_R2.md` §3 and §7(a)10. Earlier
sections, including the 2026-10-01 section, are **not edited**.

**Supersession list.** This section supersedes, where they disagree:

- §4, "a missing header, a lagging fund, malformed CSV and a schema change each produce an
  explicit record and a non-zero exit" (side observation i);
- §6, "The validation run is labelled `UNATTENDED_SCHEDULER_VALIDATION` via a one-shot
  marker that the wrapper consumes and deletes, so routine collections are never
  mislabelled" (side observation iii);
- the 2026-10-01 section's sentence "The 2026-09-20 slot has no firing record in the logs;
  it predates the current trigger's StartBoundary" (R2-G10);
- the 2026-10-01 section's statement that the counts are derived from
  `ops/R2_FORWARD_PIT_TASK.xml`: the NATURAL boundary is now pinned in `tools/reproduce.py`
  to the literal 2026-09-21T11:00:00+08:00 of D-R2-2026-10-01-02 (R2-G06). The counts are
  unchanged.

### The 2026-09-20 11:00 +08:00 slot (R2-G10)

```
SLOT_2026-09-20_11:00_+08:00 = NO_FIRING_RECORD — task registration instant not
                               established in any committed byte; not counted as a
                               missed firing and not backfilled
```

§6 records an intended first scheduled run at 2026-09-20 11:00 +08:00 (trigger
StartBoundary 2026-09-20T11:00:00+08:00). No committed byte shows whether the task was
registered before 11:00 that day, so this record does **not** assert that the slot was in
force or that it fired. The slot has no stdout line, no JSONL row and no snapshot. The
reason given on 2026-10-01 ("it predates the current trigger's StartBoundary") is withdrawn
as not applicable: that boundary came from the re-registration of 2026-09-21. No evidence
was lost either way: the endpoint state was byte-identical across the slot.
`FIRST_NATURAL_SCHEDULED_RUN = OBSERVED_FAIL_2026_09_21` means the first *observed*
firing. The 2026-09-21 11:00 slot stays `MISSING_FORWARD_CAPTURE`.

### Exit codes (side observation i)

The collector's exit code depends only on whether every fund's status is `OK` (transport
and HTTP errors set another status) and on self-verification
(`tools/collect_forward_pit.py`: status set at :474, :479, :527; `all_funds_ok` at :627;
exit at :829-835). A missing header, a lagging fund, a parse problem or a schema change is
recorded in the manifest (`missing_headers`, `notes`, `lagging_funds`,
`funds_with_parse_problems`, `schema_monitor`) **but exits 0**. The records are kept; the
"non-zero exit" claim is withdrawn.

### Validation-run label (side observation iii)

The one-shot marker did not label the 2026-09-21 19:00:42 +08:00 validation run: Windows
PowerShell 5.1 wrote it with a BOM, the wrapper rejected it and the run was recorded
`ROUTINE_FORWARD_COLLECTION` (`2026-09-21/070042_ET`, BL-R2-01; manifest not relabelled).
The wrapper reads the marker with `utf-8-sig` from FIX-R2-2026-10-02-01 onward, with a
regression test on the exact PowerShell 5.1 bytes. No installer re-run has happened since.
