<#
.SYNOPSIS
    Remove the recurring R2 forward PIT collection task.

.DESCRIPTION
    Unregisters exactly one scheduled task, "QuantTrade-R2-ForwardPIT", and
    nothing else. The name is matched exactly; no wildcard, no prefix match, no
    "clean up related tasks" behaviour.

    Data is never touched. Snapshots under data_forward_pit/ and the logs under
    logs/ are left exactly as they are -- removing the schedule stops future
    collection, it does not discard collected evidence.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File tools\remove_forward_pit_task.ps1
#>
[CmdletBinding()]
param(
    [string]$TaskName = 'QuantTrade-R2-ForwardPIT'
)

$ErrorActionPreference = 'Stop'

if ($TaskName -ne 'QuantTrade-R2-ForwardPIT') {
    Write-Output "Refusing: this script removes only 'QuantTrade-R2-ForwardPIT'."
    Write-Output "Requested '$TaskName' was not removed."
    exit 2
}

$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if (-not $task) {
    Write-Output "Task '$TaskName' is not registered. Nothing to do."
    exit 0
}

Write-Output "Removing scheduled task '$TaskName'..."
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false

$still = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($still) { throw "task '$TaskName' is still registered after removal" }

Write-Output "Removed. Collected snapshots and logs were NOT touched."
Write-Output "  snapshots: data_forward_pit/"
Write-Output "  logs     : logs/forward_pit_scheduler.jsonl"
exit 0
