@echo off
rem The sanctioned hardened form, spelled once. QROS-CF Root A.
rem -I supplies -E -s -P; -S stops site processing; -B writes no bytecode.
rem The unflagged form is NOT sanctioned and fails closed by design.
python -I -S -B "%~dp0run_governed.py" %*
