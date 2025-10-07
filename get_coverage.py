import coverage
import pytest
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def measure_coverage():
    print("Измерение Code Coverage...")

    cov = coverage.Coverage(
        source=['.'],
        omit=['*test*', '*venv*', '*__pycache__*']
    )

    cov.start()

    try:
        print("Запуск тестов...")
        pytest.main(['test_pizza_system.py', '-v'])
    except Exception as e:
        print(f"Ошибка при запуске тестов: {e}")
    finally:
        cov.stop()
        cov.save()

    print("\n" + "=" * 70)
    print("ОТЧЕТ О ПОКРЫТИИ КОДА (CODE COVERAGE)")
    print("=" * 70)

    cov.report()

    cov.html_report(directory='htmlcov')
    print(f"\nПодробный HTML отчет: htmlcov/index.html")

    print("\nДЕТАЛЬНАЯ СТАТИСТИКА:")
    analyzed_files = cov.get_data().measured_files()
    print(f"Проанализировано файлов: {len(analyzed_files)}")

    for file in analyzed_files:
        if 'pizza_project' in file:
            analysis = cov.analysis(file)
            print(f"\nФайл: {os.path.basename(file)}")
            print(f"  Строк кода: {len(analysis[1])}")
            print(f"  Пропущено строк: {len(analysis[3])}")
            if len(analysis[1]) > 0:
                coverage_percent = (len(analysis[1]) - len(analysis[3])) / len(analysis[1]) * 100
                print(f"  Покрытие: {coverage_percent:.1f}%")


if __name__ == "__main__":

    measure_coverage()
