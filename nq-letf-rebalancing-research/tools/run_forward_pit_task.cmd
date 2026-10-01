@echo off
REM ---------------------------------------------------------------------------
REM R2 forward PIT collection - Task Scheduler entry point.
REM
REM Exists only to capture stdout and stderr to a file. Task Scheduler cannot
REM redirect streams itself, and a scheduled run has no console, so without this
REM an interpreter-level failure (bad path, missing module) would leave no trace
REM at all -- the one failure mode the JSONL log cannot record, because the
REM Python process never starts.
REM
REM %1 = full path to the Python interpreter (resolved and recorded by
REM      install_forward_pit_task.ps1). Falls back to the py launcher.
REM %2 = optional capture type label. The scheduled task passes nothing, so a
REM      scheduled run is ROUTINE_FORWARD_COLLECTION. A manual validation run
REM      passes SCHEDULER_VALIDATION so it is never mistaken for routine
REM      collection evidence.
REM
REM Exit code is propagated unchanged so Task Scheduler's Last Run Result is
REM truthful. Nothing here ever suppresses a failure.
REM ---------------------------------------------------------------------------
setlocal

set "PY=%~1"
if "%PY%"=="" set "PY=py"

set "CAPTURE=%~2"
if "%CAPTURE%"=="" set "CAPTURE=ROUTINE_FORWARD_COLLECTION"

set "TOOLS=%~dp0"
set "PROJ=%TOOLS%.."
set "LOGDIR=%PROJ%\logs"
set "LOG=%LOGDIR%\forward_pit_task_stdout.log"

if not exist "%LOGDIR%" mkdir "%LOGDIR%"

echo.>> "%LOG%"
echo ==== task start %DATE% %TIME% interpreter=%PY% capture=%CAPTURE% ====>> "%LOG%"

"%PY%" "%TOOLS%run_forward_pit_scheduled.py" --scheduled-local-time 11:00 --capture-type "%CAPTURE%" >> "%LOG%" 2>&1
set "RC=%ERRORLEVEL%"

echo ==== task end   %DATE% %TIME% exit=%RC% ====>> "%LOG%"

exit /b %RC%
