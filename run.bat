@echo off
chcp 65001 > nul
title Калькулятор аналитической геометрии (Глава 4: Плоскости и прямые)
echo Запуск приложения...
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Произошла ошибка при запуске. Убедитесь, что установлены необходимые зависимости:
    echo pip install -r requirements.txt
    pause
)
