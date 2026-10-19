@echo off
rem Copy the framework and an app to the Circuit Playground Express.
rem
rem   deploy            copy cmu_playground.mpy and code.py to D:
rem   deploy test1      ... but install tests\test_playground_1.py as code.py
rem   deploy test2      ... but install tests\test_playground_2.py as code.py
rem
rem Set CIRCUITPY to use a drive other than D:, e.g.  set CIRCUITPY=E:
rem
rem This copies the existing cmu_playground.mpy. After editing
rem cmu_playground.py, run build.cmd first (or "build deploy").

setlocal
cd /d "%~dp0"
if "%CIRCUITPY%"=="" set CIRCUITPY=D:

if not exist "%CIRCUITPY%\boot_out.txt" (
    echo No CIRCUITPY drive found at %CIRCUITPY%
    exit /b 1
)

if exist "%CIRCUITPY%\cmu_playground.py" (
    echo WARNING: %CIRCUITPY%\cmu_playground.py exists and will be imported instead
    echo of cmu_playground.mpy, then run out of memory. Delete it from the board.
)

set APP=code.py
if /i "%1"=="test1" set APP=tests\test_playground_1.py
if /i "%1"=="test2" set APP=tests\test_playground_2.py

copy /y cmu_playground.mpy "%CIRCUITPY%\cmu_playground.mpy" >nul || exit /b 1
copy /y "%APP%" "%CIRCUITPY%\code.py" >nul || exit /b 1
echo Deployed cmu_playground.mpy and %APP% to %CIRCUITPY%
