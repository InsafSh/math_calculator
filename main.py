"""
Запуск приложения "Калькулятор Главы 4: Плоскости и прямые в пространстве"
"""

import sys
import os

# Добавляем текущую директорию в sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import main

if __name__ == "__main__":
    main()