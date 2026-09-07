@echo off
rem Start the trusted launch parent under -S so no .pth executes in it either.
rem QROS-CF F01/F02 pre-cert repair. See scripts/run_governed.py for why.
python -S -E -B "%~dp0run_governed.py" %*
