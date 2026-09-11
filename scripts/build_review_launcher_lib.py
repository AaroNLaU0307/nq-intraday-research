# -*- coding: utf-8 -*-
"""The reviewer's launch entrypoint, emitted into the bundle as `run_review.cmd`.

WHY A .cmd AND NOT AN INSTRUCTION. Two seats failed to start the review: the
first because `python` and `py` were not on their PATH, the second on the exact
host-local interpreter path, because the only invocable route to that
interpreter is a Windows App Execution Alias. So the delivery must carry its
own way in. `cmd.exe` is part of Windows; nothing else is assumed.

WHAT IT WILL NOT DO. It does not search PATH, does not consult the `py`
launcher, does not install anything and does not reach the network. It resolves
ONE relative path to the runtime that travels beside the bundle, checks that
runtime against a digest fixed at cut time, and refuses rather than guessing.

WHY `certutil` HASHES THE MANIFEST. Using the runtime's own Python to certify
the runtime would be circular in the only case that matters. `certutil` ships
with Windows and is independent of the runtime, so the FIRST check on the
runtime is made by something the runtime did not provide. (Against adversarial
in-process code this proves nothing -- the project's ratified threat model,
L6 R18, already puts that out of scope. Against drift, truncation and a
half-copied tree, which is what actually happens, it is exactly the check.)

WHY IT CLEARS FOUR VARIABLES. `PYTHONPATH`, `PYTHONHOME`, `PYTHONSTARTUP` and
`PYTEST_ADDOPTS` are on the project's own `HOSTILE_ENV_VARS` list
(`src/itsf/execution_identity.py`). The launcher CLEARS them, which is the
opposite of setting them: the reviewer's shell cannot perturb the run, and the
project's own ENVIRONMENT_GATE stays satisfiable. `-s` keeps the host's user
site-packages out; the pinned set lives inside the runtime's own
`Lib\\site-packages`, so no variable is needed to find it.

WHY `-B`. Without it the review WRITES bytecode into the runtime it is running
on -- measured: 121 `__pycache__` directories appeared inside the runtime, each
`.pyc` embedding its own absolute path and none of them declared in
`RUNTIME_MANIFEST.json`. A runtime that mutates while the review runs cannot be
verified afterwards, so `-B` makes it immutable for the duration. The same flag
also stops the `__pycache__` writes into the interpreter's own directories that
B-39 recorded; that row stays OPEN, because the guard still PERMITS such writes
-- this run simply no longer makes any.
"""
TEMPLATE = r"""@echo off
setlocal EnableExtensions EnableDelayedExpansion
rem ===================================================================
rem  @@REVIEW_ID@@ -- review entrypoint.
rem
rem  Run this. Nothing else is required, and no Python needs to be on
rem  your PATH:
rem
rem      run_review.cmd
rem
rem  It refuses rather than guessing. Every refusal below is a DELIVERY
rem  failure to report, not something to work around.
rem ===================================================================

set "BUNDLE=%~dp0"
if "%BUNDLE:~-1%"=="\" set "BUNDLE=%BUNDLE:~0,-1%"
set "RUNTIME=%BUNDLE%\..\@@RUNTIME_ID@@"
set "EXPECTED=@@RUNTIME_MANIFEST_SHA256@@"

rem -- the reviewer's environment must not reach the run ---------------
rem  These four are the project's own HOSTILE_ENV_VARS. Clearing them is
rem  the opposite of setting them.
set "PYTHONPATH="
set "PYTHONHOME="
set "PYTHONSTARTUP="
set "PYTEST_ADDOPTS="

set "PY=%RUNTIME%\python\python.exe"
if not exist "%PY%" (
  echo DELIVERY FAILURE: the review runtime is missing.
  echo   expected: %PY%
  echo The runtime travels BESIDE this bundle as @@RUNTIME_ID@@. Do not
  echo substitute another Python: report this and stop.
  exit /b 90
)
if not exist "%RUNTIME%\RUNTIME_MANIFEST.json" (
  echo DELIVERY FAILURE: the runtime has no RUNTIME_MANIFEST.json.
  exit /b 91
)

rem -- check the runtime with a hasher the runtime did not provide -----
set "GOT="
for /f "skip=1 tokens=*" %%H in ('certutil -hashfile "%RUNTIME%\RUNTIME_MANIFEST.json" SHA256') do (
  if not defined GOT set "GOT=%%H"
)
set "GOT=%GOT: =%"
if /i not "%GOT%"=="%EXPECTED%" (
  echo DELIVERY FAILURE: the review runtime is not the one this bundle was
  echo cut against.
  echo   expected RUNTIME_MANIFEST_SHA256 = %EXPECTED%
  echo   found                            = %GOT%
  echo Report this and stop. Do not run the review against an unverified
  echo runtime.
  exit /b 92
)

rem -- let the runtime prove its own 12002 files and 49 pinned versions
echo [runtime] verifying %RUNTIME%
"%PY%" -s -B "%RUNTIME%\verify_runtime.py"
if errorlevel 1 (
  echo DELIVERY FAILURE: the runtime failed its own identity check above.
  exit /b 93
)

rem -- the review itself -----------------------------------------------
rem  The runner resolves, creates and PROVES its own seat-native output
rem  root before it arms the guard, and prints where it is. Nothing is
rem  written inside this delivery: if the output root cannot be
rem  established the runner stops and says so.
echo [runtime] OK -- starting the guarded review
"%PY%" -s -B "%BUNDLE%\run_bundle_tests.py"
set "RC=%ERRORLEVEL%"
echo [review] run_bundle_tests.py exit code %RC%
echo.
echo Your INITIAL_FINDINGS.md, FREEZE.json and ATTESTATION.md go in the
echo review output root printed above, NOT in this delivery, which is
echo immutable. That directory is bound to this delivery by its own
echo OUTPUT_BINDING.json.
exit /b %RC%
"""


def render(profile: dict) -> str:
    rt = profile["review_runtime"]
    body = TEMPLATE
    body = body.replace("@@REVIEW_ID@@", profile["review_id"])
    body = body.replace("@@RUNTIME_ID@@", rt["runtime_id"])
    body = body.replace("@@RUNTIME_MANIFEST_SHA256@@",
                        rt["runtime_manifest_sha256"])
    assert "@@" not in body
    return body.replace("\r\n", "\n").replace("\n", "\r\n")
