@echo off
chcp 65001 > nul
title MathCalc
echo Запуск MathCalc...
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Произошла ошибка при запуске. Убедитесь, что установлены необходимые зависимости:
    echo pip install -r requirements.txt
    pause
)
