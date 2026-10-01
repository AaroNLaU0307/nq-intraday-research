<#
.SYNOPSIS
    Install the recurring R2 forward PIT collection task.

.DESCRIPTION
    Registers a single Windows Scheduled Task, "QuantTrade-R2-ForwardPIT", that
    runs the forward PIT collector once per CALENDAR day at a fixed local time.

    TWO EXPLICIT MODES
    ------------------
    UNATTENDED_PASSWORD  (default, preferred)
        "Run whether user is logged on or not", backed by the account password,
        registered under Aaron's own user identity. Runs with no interactive
        desktop session and retains normal network capability.

    INTERACTIVE_TOKEN    (fallback, must be requested explicitly)
        Runs only while the user has an interactive logon session. This is a
        real capability reduction and is NEVER selected automatically: if
        unattended registration fails, this script FAILS LOUDLY rather than
        quietly downgrading and reporting success.

    S4U IS NOT SUPPORTED AND MUST NOT BE USED
    -----------------------------------------
    S4U ("run whether logged on or not" WITHOUT a stored password) issues a
    logon token with no network credentials. This collector's entire purpose is
    outbound HTTPS to a public endpoint, so S4U is the wrong fit. The earlier
    suggestion to upgrade to S4U is withdrawn.

        S4U_UPGRADE_FOR_FORWARD_COLLECTOR = FORBIDDEN_WRONG_FIT

    CREDENTIAL SAFETY
    -----------------
    The password is prompted for locally and securely (Read-Host
    -AsSecureString), never echoed. The ScheduledTasks API requires a plaintext
    string, so the value is marshalled out of the SecureString only inside the
    registration call and the unmanaged buffer is zeroed in a finally block. It
    is never written to disk, never placed on a command line, never logged,
    never printed, and never stored in any project file.

.PARAMETER Mode
    UNATTENDED_PASSWORD (default) | INTERACTIVE_TOKEN | PREFLIGHT

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File tools\install_forward_pit_task.ps1
#>
[CmdletBinding()]
param(
    [ValidateSet('UNATTENDED_PASSWORD', 'INTERACTIVE_TOKEN', 'PREFLIGHT', 'VERIFY')]
    [string]$Mode        = 'UNATTENDED_PASSWORD',
    # Supplied interactively by default. NEVER hard-code a real address here and
    # never persist it: it is used only to build the in-process principal string.
    [string]$MicrosoftAccountEmail = '',
    [string]$TaskName    = 'QuantTrade-R2-ForwardPIT',
    [string]$LocalTime   = '11:00',
    [string]$PythonPath  = '',
    [string]$ExportXml   = '',
    [switch]$SkipValidationRun
)

$ErrorActionPreference = 'Stop'

$ToolsDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ToolsDir
$CmdPath    = Join-Path $ToolsDir 'run_forward_pit_task.cmd'
$WrapperPy  = Join-Path $ToolsDir 'run_forward_pit_scheduled.py'
$OpsDir     = Join-Path $ProjectDir 'ops'
$LogDir     = Join-Path $ProjectDir 'logs'
if (-not $ExportXml) { $ExportXml = Join-Path $OpsDir 'R2_FORWARD_PIT_TASK.xml' }

Write-Output "R2 forward PIT task installer"
Write-Output "  mode       : $Mode"
Write-Output "  project    : $ProjectDir"
Write-Output "  task name  : $TaskName"
Write-Output "  local time : $LocalTime daily (every calendar day)"

foreach ($required in @($CmdPath, $WrapperPy)) {
    if (-not (Test-Path $required)) { throw "missing required file: $required" }
}

# --------------------------------------------------------------------------- #
# 1. Identity
# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #
# Identity: the LOCAL PROFILE IDENTITY and the PASSWORD AUTHENTICATION PRINCIPAL
# are NOT necessarily the same string.
#
#   local profile identity          DESKTOP-XXXX\Aaron   (NTAccount form)
#   password auth principal (MSA)   MicrosoftAccount\<account email>
#
# For a Microsoft-Account-backed profile the NTAccount form authenticates an
# interactive token perfectly well, but it is NOT the principal that the account
# password authenticates. Registering a password-backed task against it fails.
# That mismatch was the root cause of the earlier registration failure -- not a
# wrong password.
# --------------------------------------------------------------------------- #

function Format-RedactedPrincipal {
    # Never print or persist a full account email.
    param([string]$Id)
    if ([string]::IsNullOrWhiteSpace($Id)) { return '<none>' }
    if ($Id -match '@') {
        $prefix = ''
        if ($Id -match '^(?<p>[^\\]+\\)') { $prefix = $Matches['p'] }
        return ($prefix + '<redacted-account-email>')
    }
    return $Id
}

Write-Output "Resolving identity..."
$LocalProfileIdentity = "$env:USERDOMAIN\$env:USERNAME"
Write-Output "  local profile identity : $LocalProfileIdentity"

$PrincipalSource = 'Unknown'
try {
    $localUser = Get-LocalUser -Name $env:USERNAME -ErrorAction Stop
    $PrincipalSource = [string]$localUser.PrincipalSource
} catch {
    Write-Output "  (Get-LocalUser unavailable: $($_.Exception.Message))"
}
Write-Output "  PrincipalSource        : $PrincipalSource"

$MicrosoftAccountMode = ($PrincipalSource -eq 'MicrosoftAccount')
if ($MicrosoftAccountMode) {
    Write-Output "  MICROSOFT_ACCOUNT_PRINCIPAL_MODE = YES"
    Write-Output "  -> password-backed registration must use MicrosoftAccount\<email>,"
    Write-Output "     NOT $LocalProfileIdentity"
} else {
    Write-Output "  MICROSOFT_ACCOUNT_PRINCIPAL_MODE = NO (local account principal)"
}

# $UserId is resolved per-mode below; for non-password modes the local profile
# identity is correct and sufficient.
$UserId = $LocalProfileIdentity

# --------------------------------------------------------------------------- #
# 2. Local-availability check (OneDrive Files-On-Demand)
# --------------------------------------------------------------------------- #
# A task with no interactive session must not depend on the OneDrive sync client
# to materialise a placeholder. Every required file must already be local.

Write-Output "Checking required files are locally available (not online-only placeholders)..."
$OFFLINE = 0x1000; $RECALL_OPEN = 0x40000; $RECALL_DATA = 0x400000
$placeholders = @()
foreach ($f in @($CmdPath, $WrapperPy, (Join-Path $ToolsDir 'collect_forward_pit.py'))) {
    $item = Get-Item $f -Force
    $attr = [int]$item.Attributes
    if ((($attr -band $OFFLINE) -ne 0) -or (($attr -band $RECALL_OPEN) -ne 0) -or
        (($attr -band $RECALL_DATA) -ne 0) -or ($item.Length -eq 0)) {
        $placeholders += $item.FullName
    }
}
if ($placeholders.Count -gt 0) {
    Write-Output "  BLOCKER: these files are online-only placeholders or empty:"
    $placeholders | ForEach-Object { Write-Output "    $_" }
    throw "required project files are not locally available. Make them 'Always keep on this device' in OneDrive, then re-run. The project was NOT moved."
}
Write-Output "  all required files are local."

# --------------------------------------------------------------------------- #
# 3. Resolve the interpreter mechanically
# --------------------------------------------------------------------------- #

function Test-Interpreter {
    param([string]$Path)
    if (-not $Path) { return $false }
    if (-not (Test-Path $Path)) { return $false }
    $item = Get-Item $Path -Force
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
        Write-Output "  rejected (Store alias / reparse point): $Path"
        return $false
    }
    if ($item.Length -eq 0) {
        Write-Output "  rejected (zero length): $Path"
        return $false
    }
    # Must import everything the collector needs, including the IANA tz database:
    # Windows ships none, so this is a real failure mode.
    & $Path -c "import urllib.request, json, hashlib, csv; from zoneinfo import ZoneInfo; ZoneInfo('America/New_York')" 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Output "  rejected (cannot import collector prerequisites incl. zoneinfo): $Path"
        return $false
    }
    return $true
}

Write-Output "Resolving interpreter..."
$candidates = @()
if ($PythonPath) { $candidates += $PythonPath }
$candidates += (Get-ChildItem -Path "$env:LOCALAPPDATA\Programs\Python" -Filter 'python.exe' `
                    -Recurse -Depth 1 -ErrorAction SilentlyContinue |
                    Sort-Object FullName -Descending | ForEach-Object { $_.FullName })
$candidates += @(
    'C:\Program Files\Python313\python.exe',
    'C:\Program Files\Python312\python.exe'
)
$cmdPython = (Get-Command python -ErrorAction SilentlyContinue)
if ($cmdPython) { $candidates += $cmdPython.Source }

$Interpreter = $null
foreach ($candidate in ($candidates | Select-Object -Unique)) {
    if (Test-Interpreter -Path $candidate) { $Interpreter = $candidate; break }
}
if (-not $Interpreter) {
    throw "no usable Python interpreter found. Pass -PythonPath explicitly. A Windows Store alias will not be accepted."
}
$pyVersion = (& $Interpreter -c "import platform;print(platform.python_version())").Trim()
Write-Output "  interpreter: $Interpreter  (Python $pyVersion)"

# --------------------------------------------------------------------------- #
# 4. Build the task definition (identical in both modes)
# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #
# Action arguments: cmd.exe outer-quoting
# --------------------------------------------------------------------------- #
# The project path contains a space ("Quant trade"). The naive form
#     /c "<script>" "<python>"
# makes cmd.exe strip the quotes and break the command at the first space:
#     'C:\Users\Aaron\OneDrive\Desktop\Quant' is not recognized ...  (exit 1)
# The correct form doubles the outer quotes and adds /s, so cmd.exe strips only
# the outermost pair and takes the remainder verbatim. /d also skips AutoRun, so
# a machine-local AutoRun value cannot inject itself into an unattended run.
#
# The string is built by tools\task_action.py -- the single source of truth,
# covered by tools\test_task_action.py including a negative control that proves
# the old form really fails. Deriving the quoting here as well is exactly how
# this defect would come back, so it is deliberately NOT re-derived.

$TaskActionPy = Join-Path $ToolsDir 'task_action.py'
if (-not (Test-Path $TaskActionPy)) { throw "missing required file: $TaskActionPy" }

$ActionArguments = (& $Interpreter $TaskActionPy --script $CmdPath --interpreter $Interpreter)
if ($LASTEXITCODE -ne 0 -or -not $ActionArguments) {
    throw "could not build the task action arguments via task_action.py"
}
$ActionArguments = [string]$ActionArguments

# Validate the SHAPE here rather than round-tripping the string back through a
# native command: PowerShell re-splits a quote-laden argument, which would
# corrupt exactly the quoting under test.
$expectedArgs = '/d /s /c ""' + $CmdPath + '" "' + $Interpreter + '""'
if ($ActionArguments -cne $expectedArgs) {
    throw ("task_action.py produced an unexpected argument string." +
           " got [$ActionArguments] expected [$expectedArgs]")
}
if ($ActionArguments -notmatch '^/d /s /c ""' -or $ActionArguments -notmatch '""$') {
    throw "constructed action arguments failed the quoting shape check: [$ActionArguments]"
}
Write-Output "  action args validated: $ActionArguments"

$action = New-ScheduledTaskAction -Execute 'cmd.exe' `
    -Argument $ActionArguments `
    -WorkingDirectory $ProjectDir

$trigger = New-ScheduledTaskTrigger -Daily -At $LocalTime

# StartWhenAvailable: a machine that was off at the scheduled time still runs the
#   task when it next can. The collector records the REAL time, never the
#   scheduled one, and never fabricates a snapshot for a day that was missed.
# IgnoreNew: a second instance is dropped rather than run in parallel. The
#   wrapper also holds its own lock, so this is defence in depth.
# Battery flags are task-scoped; no system power setting is modified.
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -RestartCount 0

$description = ("R2 forward point-in-time ETF fund-size collection. " +
                "Data-preservation infrastructure only: it does not repair 2010-2021, " +
                "assigns no sample tier, and authorizes no research.")

if ($Mode -eq 'VERIFY') {
    # Read-only inspection of an existing registration. Prints a REDACTED
    # principal so a Microsoft account email is never surfaced or copied into a
    # report, while still proving the logon type and run level.
    $t = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if (-not $t) { Write-Output "TASK_EXISTS = NO"; return }
    $ti = Get-ScheduledTaskInfo -TaskName $TaskName
    Write-Output ""
    Write-Output "VERIFY (read-only)"
    Write-Output ("  TASK_EXISTS                      = YES")
    Write-Output ("  TASK_ENABLED                     = {0}" -f $(if ($t.State -ne 'Disabled') {'YES'} else {'NO'}))
    Write-Output ("  TASK_STATE                       = {0}" -f $t.State)
    Write-Output ("  TASK_PRINCIPAL (redacted)        = {0}" -f (Format-RedactedPrincipal $t.Principal.UserId))
    Write-Output ("  TASK_PRINCIPAL_IS_MSA_FORM       = {0}" -f $(if ($t.Principal.UserId -match '@') {'YES'} else {'NO'}))
    Write-Output ("  TASK_LOGON_TYPE                  = {0}" -f $t.Principal.LogonType)
    Write-Output ("  TASK_RUNLEVEL                    = {0}" -f $t.Principal.RunLevel)
    Write-Output ("  RUN_WHILE_USER_LOGGED_OUT        = {0}" -f $(if ($t.Principal.LogonType -eq 'Password') {'YES'} else {'NO'}))
    Write-Output ("  START_WHEN_AVAILABLE             = {0}" -f $t.Settings.StartWhenAvailable)
    Write-Output ("  MULTIPLE_INSTANCES               = {0}" -f $t.Settings.MultipleInstancesPolicy)
    Write-Output ("  EXECUTION_TIME_LIMIT             = {0}" -f $t.Settings.ExecutionTimeLimit)
    Write-Output ("  NEXT_RUN_TIME                    = {0}" -f $ti.NextRunTime)
    Write-Output ("  LAST_RUN_TIME                    = {0}" -f $ti.LastRunTime)
    Write-Output ("  LAST_TASK_RESULT                 = {0}" -f $ti.LastTaskResult)
    return
}

if ($Mode -eq 'PREFLIGHT') {
    Write-Output ""
    Write-Output "PREFLIGHT ONLY - nothing was registered."
    Write-Output "  action    : cmd.exe $ActionArguments"
    Write-Output "  workdir   : $ProjectDir"
    if ($MicrosoftAccountMode) {
        Write-Output "  principal : MicrosoftAccount\<account email>  (target logon type: Password)"
        Write-Output "              NOT $LocalProfileIdentity - that form authenticates an"
        Write-Output "              interactive token but not the Microsoft account password."
        Write-Output "              The email is prompted for locally at install time."
    } else {
        Write-Output "  principal : $UserId (target logon type: Password)"
    }
    Write-Output "  trigger   : daily at $LocalTime, every calendar day"
    Write-Output "  READY for UNATTENDED_PASSWORD registration."
    return
}

# --------------------------------------------------------------------------- #
# 5. Register
# --------------------------------------------------------------------------- #
# RunLevel Limited throughout: this task needs local project-file access, normal
# outbound HTTPS and Task Scheduler execution. Nothing requires elevation, so
# "run with highest privileges" is deliberately NOT enabled.

$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Output "Existing task found; it will be replaced (never duplicated)."
}

if ($Mode -eq 'UNATTENDED_PASSWORD') {

    if (-not [Environment]::UserInteractive) {
        throw ("cannot prompt for a credential in a non-interactive host. " +
               "MANUAL_SECURE_CREDENTIAL_STEP_REQUIRED: run this script yourself " +
               "from an ordinary local PowerShell window.")
    }

    # ----- resolve the PASSWORD AUTHENTICATION PRINCIPAL --------------------
    if ($MicrosoftAccountMode) {
        if (-not $MicrosoftAccountEmail) {
            Write-Output ""
            Write-Output "This Windows profile is backed by a MICROSOFT ACCOUNT."
            Write-Output "Password-backed task registration must therefore authenticate as"
            Write-Output "  MicrosoftAccount\<your account email>"
            Write-Output "and NOT as $LocalProfileIdentity."
            Write-Output ""
            Write-Output "The email is not a secret, so it is shown as you type. It is used"
            Write-Output "only to build the principal string in memory and is not written to"
            Write-Output "any project file, log or task XML."
            Write-Output ""
            $MicrosoftAccountEmail = (Read-Host -Prompt "Microsoft account email for Windows user $env:USERNAME").Trim()
        }
        if (-not $MicrosoftAccountEmail -or $MicrosoftAccountEmail -notmatch '^[^@\s]+@[^@\s]+\.[^@\s]+$') {
            throw "a valid Microsoft account email is required for MICROSOFT_ACCOUNT_PRINCIPAL_MODE; nothing was registered."
        }
        $UserId = "MicrosoftAccount\$MicrosoftAccountEmail"
        Write-Output "  password auth principal: MicrosoftAccount\<redacted-account-email>"
    } else {
        $UserId = $LocalProfileIdentity
        Write-Output "  password auth principal: $UserId"
    }

    # ----- secure password prompt ------------------------------------------
    Write-Output ""
    Write-Output "Unattended registration needs the Windows ACCOUNT PASSWORD."
    Write-Output "  * Typed here, in your local PowerShell window, and not echoed."
    Write-Output "  * Never written to any file, log, XML, or command line."
    Write-Output "  * A Windows Hello PIN will NOT work; use the account password."
    Write-Output ""

    $secure = Read-Host -Prompt "Windows password for $(Format-RedactedPrincipal $UserId)" -AsSecureString
    if (-not $secure -or $secure.Length -eq 0) {
        throw "no credential supplied; nothing was registered."
    }

    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try {
        $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
        # -Password is a cmdlet parameter inside this process. It never appears
        # in a command line, process listing, or shell history.
        Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
            -Settings $settings -Description $description `
            -User $UserId -Password $plain -RunLevel Limited -Force | Out-Null
    } catch {
        # FAIL CLOSED. No fallback to the local NTAccount form, no fallback to
        # InteractiveToken. A silent downgrade that reports success is exactly
        # the defect this repair exists to remove.
        throw ("UNATTENDED_PASSWORD registration FAILED for principal " +
               (Format-RedactedPrincipal $UserId) + ": " + $_.Exception.Message +
               "  -- NO fallback was applied. The task was not downgraded to " +
               "InteractiveToken and not re-pointed at $LocalProfileIdentity. " +
               "Any previously working registration is unchanged.")
    } finally {
        if ($bstr -ne [IntPtr]::Zero) {
            [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
        }
        Set-Variable -Name plain -Value $null -Scope Local -ErrorAction SilentlyContinue
        Remove-Variable -Name plain -Scope Local -ErrorAction SilentlyContinue
        $secure.Dispose()
        [GC]::Collect()
    }
    Write-Output "  registered: LogonType Password (runs whether logged on or not)"

} elseif ($Mode -eq 'INTERACTIVE_TOKEN') {

    Write-Output ""
    Write-Output "WARNING: INTERACTIVE_TOKEN was requested EXPLICITLY."
    Write-Output "  The task will run ONLY while you have an interactive Windows session."
    Write-Output "  RUN_WHILE_USER_LOGGED_OUT = NO"
    $principal = New-ScheduledTaskPrincipal -UserId $UserId `
        -LogonType Interactive -RunLevel Limited
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
        -Settings $settings -Principal $principal -Description $description -Force | Out-Null
    Write-Output "  registered: LogonType Interactive (reduced capability, explicitly chosen)"
}

# --------------------------------------------------------------------------- #
# 6. Verify
# --------------------------------------------------------------------------- #

$task = Get-ScheduledTask -TaskName $TaskName
$info = Get-ScheduledTaskInfo -TaskName $TaskName
$logon = $task.Principal.LogonType

Write-Output ""
Write-Output "VERIFICATION"
Write-Output ("  TaskName          : {0}" -f $task.TaskName)
Write-Output ("  State             : {0}" -f $task.State)
Write-Output ("  Principal         : {0}" -f (Format-RedactedPrincipal $task.Principal.UserId))
Write-Output ("  PrincipalIsMsaForm: {0}" -f $(if ($task.Principal.UserId -match '@') {'YES'} else {'NO'}))
Write-Output ("  LogonType         : {0}" -f $logon)
Write-Output ("  RunLevel          : {0}" -f $task.Principal.RunLevel)
Write-Output ("  NextRunTime       : {0}" -f $info.NextRunTime)
Write-Output ("  Execute           : {0}" -f $task.Actions[0].Execute)
Write-Output ("  Arguments         : {0}" -f $task.Actions[0].Arguments)
Write-Output ("  WorkingDirectory  : {0}" -f $task.Actions[0].WorkingDirectory)
Write-Output ("  Interpreter       : {0} (Python {1})" -f $Interpreter, $pyVersion)
Write-Output ("  StartWhenAvailable: {0}" -f $task.Settings.StartWhenAvailable)
Write-Output ("  MultipleInstances : {0}" -f $task.Settings.MultipleInstancesPolicy)
Write-Output ("  ExecutionTimeLimit: {0}" -f $task.Settings.ExecutionTimeLimit)

$duplicates = @(Get-ScheduledTask | Where-Object { $_.TaskName -eq $TaskName })
Write-Output ("  DuplicateTasks    : {0}" -f ($duplicates.Count - 1))

# Verify what Windows actually STORED, not what we asked for. A stored action
# that lost its outer quoting fails silently at run time, producing no output at
# all -- the precise failure mode this check exists to prevent.
$storedArgs = $task.Actions[0].Arguments
# Exact, case-sensitive equality with the string we constructed. Stronger than a
# shape check: it catches Windows normalising, trimming or re-quoting the value.
if ($storedArgs -cne $ActionArguments) {
    throw ("STORED task action arguments differ from what was registered." +
           " stored=[$storedArgs] expected=[$ActionArguments]")
}
if ($storedArgs -notmatch '^/d /s /c ""' -or $storedArgs -notmatch '""$') {
    throw "STORED task action arguments are not canonical: [$storedArgs]"
}
Write-Output ("  StoredArgsCanonical: YES")
Write-Output ("  StoredArguments   : {0}" -f $storedArgs)

if ($Mode -eq 'UNATTENDED_PASSWORD' -and $logon -ne 'Password') {
    throw "expected LogonType Password but found '$logon'. Not accepting a silent downgrade."
}

# --------------------------------------------------------------------------- #
# 7. Export the definition, then scan it for secrets
# --------------------------------------------------------------------------- #
# Windows stores the task credential as an LSA secret, NOT in the task XML. The
# export is scanned anyway rather than assumed clean.

if (-not (Test-Path $OpsDir)) { New-Item -ItemType Directory -Path $OpsDir | Out-Null }
Export-ScheduledTask -TaskName $TaskName | Out-File -FilePath $ExportXml -Encoding utf8
$xmlText = Get-Content $ExportXml -Raw
$leak = $false
foreach ($pattern in @('<Password', 'Password>', 'cpassword', 'SecureString')) {
    if ($xmlText -match [regex]::Escape($pattern)) { $leak = $true; Write-Output "  XML SECRET SCAN: found '$pattern'" }
}
if ($leak) {
    Remove-Item $ExportXml -Force
    throw "exported task XML appeared to contain credential material; the export was DELETED. Use ops/R2_FORWARD_PIT_TASK.template.xml as the declarative reference instead."
}
Write-Output ("  Exported XML      : {0}  (secret scan: clean)" -f $ExportXml)

# --------------------------------------------------------------------------- #
# 8. Validate in the task's own logon context
# --------------------------------------------------------------------------- #
# Starting the registered task exercises the REAL principal: its network access,
# its filesystem access and the whole wrapper chain. It does NOT prove Windows
# will wake and fire the task at a future wall-clock time -- that remains a
# separate operational observation.

if ($SkipValidationRun) {
    Write-Output ""
    Write-Output "Validation run skipped by request."
    Write-Output "Installed."
    return
}

Write-Output ""
Write-Output "Validating in the task's own logon context (Start-ScheduledTask)..."
$logPath = Join-Path $LogDir 'forward_pit_scheduler.jsonl'
$before = 0
if (Test-Path $logPath) { $before = (Get-Content $logPath | Measure-Object -Line).Lines }

# Label the run that Task Scheduler is about to launch. The marker is one-shot:
# the wrapper deletes it on read, so routine collections are never mislabelled.
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }
$marker = Join-Path $LogDir '.capture_type_once'
$markerPayload = @{
    capture_type = 'UNATTENDED_SCHEDULER_VALIDATION'
    written_utc  = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
} | ConvertTo-Json -Compress
Set-Content -Path $marker -Value $markerPayload -Encoding utf8

Start-ScheduledTask -TaskName $TaskName
$deadline = (Get-Date).AddMinutes(5)
do {
    Start-Sleep -Seconds 5
    $info = Get-ScheduledTaskInfo -TaskName $TaskName
    $state = (Get-ScheduledTask -TaskName $TaskName).State
} while ($state -eq 'Running' -and (Get-Date) -lt $deadline)

$after = 0
if (Test-Path $logPath) { $after = (Get-Content $logPath | Measure-Object -Line).Lines }

Write-Output ("  LastTaskResult    : {0}" -f $info.LastTaskResult)
Write-Output ("  LastRunTime       : {0}" -f $info.LastRunTime)
Write-Output ("  New log records   : {0}" -f ($after - $before))

if ($info.LastTaskResult -eq 0 -and $after -gt $before) {
    Write-Output "  PASSWORD_BACKED_TASK_CONTEXT_VALIDATED = YES"
    Write-Output "  (network access, project-file access and the wrapper chain all exercised"
    Write-Output "   under the registered principal)"
} else {
    Write-Output "  PASSWORD_BACKED_TASK_CONTEXT_VALIDATED = NO"
    Write-Output "  Inspect logs\forward_pit_scheduler.jsonl and logs\forward_pit_task_stdout.log"
}

Write-Output ""
Write-Output "NOTE: a manually started task proves the principal, network, filesystem and"
Write-Output "      wrapper chain. It does NOT prove Windows will fire the task at a future"
Write-Output "      wall-clock time. The first natural scheduled run remains a separate"
Write-Output "      observation: Get-ScheduledTaskInfo -TaskName $TaskName"
Write-Output ""
Write-Output "Installed. To remove: powershell -ExecutionPolicy Bypass -File tools\remove_forward_pit_task.ps1"
