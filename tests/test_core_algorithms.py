import sys
import os
import pytest
import numpy as np


current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    import sugar_core
except ImportError:
    pytest.fail("Не удалось импортировать модуль 'sugar_core'. Убедитесь, что файл .pyd/.so находится в корне проекта и скомпилирован.")

def get_counter_greedy_matrix():
    """
    Матрица 2x2, на которой жадный алгоритм ошибается.
    Оптимум: (0,1) + (1,0) = 100 + 5 = 105.
    Жадный: (0,0)[10] + (1,1)[5] = 15.
    """
    return np.array([
        [10.0, 100.0],
        [5.0,  5.0]
    ])


# --- 1. ТЕСТЫ ГЕНЕРАТОРА МАТРИЦ (MATRIX GENERATOR) ---

def test_generator_shape():
    """1. Проверка размерности создаваемой матрицы."""
    params = {
        'n': 10, 'T': 1, 'alpha_min': 0.1, 'alpha_max': 0.2,
        'beta1': 0.9, 'beta2': 0.95, 'dist_type': 'uniform',
        'use_ripening': False, 'use_inorganic': False
    }
    gen = sugar_core.MatrixGenerator(params)
    mat = gen.generate()
    assert mat.shape == (10, 10)

def test_generator_bounds_alpha():
    """2. Проверка, что начальная сахаристость (1-й столбец) в заданных пределах."""
    val = 0.5
    params = {
        'n': 50, 'T': 1, 'alpha_min': val, 'alpha_max': val,
        'beta1': 1.0, 'beta2': 1.0, 'dist_type': 'uniform',
        'use_ripening': False, 'use_inorganic': False
    }
    gen = sugar_core.MatrixGenerator(params)
    mat = gen.generate()
    assert np.allclose(mat[:, 0], val)

def test_generator_degradation():
    """3. Проверка убывания значений (деградация)."""
    params = {
        'n': 5, 'T': 1, 'alpha_min': 0.5, 'alpha_max': 0.6,
        'beta1': 0.5, 'beta2': 0.9,
        'dist_type': 'uniform',
        'use_ripening': False, 'use_inorganic': False
    }
    gen = sugar_core.MatrixGenerator(params)
    mat = gen.generate()
    for j in range(1, 5):
        assert np.all(mat[:, j] < mat[:, j-1])

def test_generator_ripening():
    """4. Проверка роста значений (дозаривание) на первых v этапах."""
    params = {
        'n': 5, 'T': 1, 'alpha_min': 0.1, 'alpha_max': 0.2,
        'beta1': 0.9, 'beta2': 0.9,
        'dist_type': 'uniform',
        'use_ripening': True, 'v': 3, 'beta_max': 1.1,
        'use_inorganic': False
    }
    gen = sugar_core.MatrixGenerator(params)
    mat = gen.generate()
    assert np.all(mat[:, 1] > mat[:, 0])
    assert np.all(mat[:, 2] > mat[:, 1])

def test_generator_inorganic_loss():
    """5. Проверка уменьшения значений при включении неорганики."""
    params = {
        'n': 5, 'T': 1, 'alpha_min': 0.5, 'alpha_max': 0.5,
        'beta1': 1.0, 'beta2': 1.0,
        'dist_type': 'uniform',
        'use_ripening': False, 'use_inorganic': False
    }
    params['use_inorganic'] = True
    gen_loss = sugar_core.MatrixGenerator(params)
    mat_loss = gen_loss.generate()
    
    assert np.all(mat_loss >= 0)
    assert np.all(mat_loss <= 1.0)
    assert np.mean(mat_loss) < 0.5

def test_generator_concentrated():
    """6. Проверка работы флага концентрированного распределения."""
    params = {
        'n': 10, 'T': 1, 'alpha_min': 0.2, 'alpha_max': 0.3,
        'beta1': 0.8, 'beta2': 0.95, 
        'dist_type': 'concentrated',
        'use_ripening': False, 'use_inorganic': False
    }
    gen = sugar_core.MatrixGenerator(params)
    mat = gen.generate()
    assert mat.shape == (10, 10)
    assert np.all(mat >= 0)


# --- 2. ТЕСТЫ ТОЧНОГО АЛГОРИТМА (ВЕНГЕРСКИЙ / EXACT) ---

def test_exact_identity():
    """1. Единичная матрица (диагональ)."""
    mat = np.eye(5) 
    res = sugar_core.solve_exact(mat)
    assert res == pytest.approx(5.0)

def test_exact_counter_greedy():
    """2. Тест на матрице, сложной для жадного алгоритма."""
    mat = get_counter_greedy_matrix()
    res = sugar_core.solve_exact(mat)
    assert res == pytest.approx(105.0)

def test_exact_simple():
    """3. Простая матрица 2x2."""
    mat = np.array([[1, 2], [3, 4]])
    assert sugar_core.solve_exact(mat) == pytest.approx(5.0)

def test_exact_zeros():
    """4. Нулевая матрица."""
    mat = np.zeros((4, 4))
    assert sugar_core.solve_exact(mat) == pytest.approx(0.0)

def test_exact_all_same():
    """5. Одинаковые значения."""
    mat = np.full((3, 3), 10.0)
    assert sugar_core.solve_exact(mat) == pytest.approx(30.0)

def test_exact_rectish_logic():
    """6. Явный максимум по диагонали."""
    mat = np.array([
        [100, 1, 1],
        [1, 100, 1],
        [1, 1, 100]
    ])
    assert sugar_core.solve_exact(mat) == pytest.approx(300.0)


# --- 3. ТЕСТЫ ЖАДНОГО АЛГОРИТМА (GREEDY) ---

def test_greedy_logic_basic():
    """1. Базовая логика."""
    mat = np.array([
        [10, 10, 5],
        [20, 20, 5],
        [30, 30, 5]
    ])
    # J0: Max 30 (R2) -> Res=30
    # J1: Max 20 (R1) -> Res=50
    # J2: Max 5  (R0) -> Res=55
    assert sugar_core.run_greedy(mat) == pytest.approx(55.0)

def test_greedy_fails():
    """2. Проверка проигрыша на контр-примере."""
    mat = get_counter_greedy_matrix()
    # J0: 10 (R0)
    # J1: 5 (R1)
    # Sum: 15
    assert sugar_core.run_greedy(mat) == pytest.approx(15.0)

def test_greedy_identity():
    """3. Единичная матрица."""
    mat = np.eye(3)
    assert sugar_core.run_greedy(mat) == pytest.approx(3.0)

def test_greedy_zeros():
    """4. Нули."""
    mat = np.zeros((5, 5))
    assert sugar_core.run_greedy(mat) == pytest.approx(0.0)

def test_greedy_increasing():
    """5. Возрастающая матрица."""
    mat = np.array([
        [1, 2],
        [3, 4]
    ])
    # J0: 3 (R1)
    # J1: 2 (R0)
    # Sum: 5
    assert sugar_core.run_greedy(mat) == pytest.approx(5.0)

def test_greedy_row_blocking():
    """6. Блокировка выгодной строки на раннем этапе."""
    mat = np.array([
        [100, 1000], 
        [50,  50]
    ])
    # J0: 100 (R0)
    # J1: 50 (R1), т.к. R0 занят
    # Sum: 150
    assert sugar_core.run_greedy(mat) == pytest.approx(150.0)


# --- 4. ТЕСТЫ БЕРЕЖЛИВОГО АЛГОРИТМА (THRIFTY) ---

def test_thrifty_logic_basic():
    """1. Базовая логика (выбор минимума)."""
    mat = np.array([
        [10, 100, 100],
        [20, 20,  100],
        [30, 30,  30]
    ])
    # J0: Min 10 (R0)
    # J1: Min 20 (R1)
    # J2: Min 30 (R2)
    # Sum: 60
    assert sugar_core.run_thrifty(mat) == pytest.approx(60.0)

def test_thrifty_vs_greedy():
    """2. Пример, где бережливый лучше (экономит ресурсы)."""
    mat = np.array([
        [1, 100],
        [10, 10]
    ])
    # Thrifty: J0->1(R0), J1->10(R1). Sum=11.
    assert sugar_core.run_thrifty(mat) == pytest.approx(11.0)

def test_thrifty_zeros():
    """3. Нули."""
    assert sugar_core.run_thrifty(np.zeros((3,3))) == 0.0

def test_thrifty_reverse_diagonal():
    """4. Обратная диагональ."""
    mat = np.array([
        [0, 0, 1],
        [0, 1, 0],
        [1, 0, 0]
    ])
    # Thrifty выберет нули на каждом шаге.
    assert sugar_core.run_thrifty(mat) == pytest.approx(0.0)

def test_thrifty_one_element():
    """5. Матрица 1x1."""
    mat = np.array([[5.0]])
    assert sugar_core.run_thrifty(mat) == pytest.approx(5.0)

def test_thrifty_large_diff():
    """6. Огромная разница в значениях."""
    mat = np.array([
        [1, 1000],
        [1000, 1]
    ])
    # J0: 1 (R0)
    # J1: 1 (R1)
    # Sum: 2
    assert sugar_core.run_thrifty(mat) == pytest.approx(2.0)


# --- 5. ТЕСТЫ МЕДИАННОГО АЛГОРИТМА (MEDIAN) ---

def test_median_odd_size():
    """1. Нечетный размер (3 элемента)."""
    mat = np.array([
        [1, 1, 1],
        [5, 5, 5],
        [10, 10, 10]
    ])
    # J0: [1, 5, 10] -> Med 5 (R1)
    # J1: [1, 10] -> Med (index 1) 10 (R2)
    # J2: [1] -> Med 1 (R0)
    # Sum: 16
    assert sugar_core.run_median(mat) == pytest.approx(16.0)

def test_median_even_size():
    """2. Четный размер."""
    mat = np.zeros((4,4))
    mat[:, 0] = [1, 2, 3, 4]
    mat[:, 1] = [1, 2, 3, 4]
    mat[:, 2] = [1, 2, 3, 4]
    mat[:, 3] = [1, 2, 3, 4]
    # Логика C++: size/2.
    # 4 -> idx 2 (Val 3)
    # 3 -> idx 1 (Val 2)
    # 2 -> idx 1 (Val 4)
    # 1 -> idx 0 (Val 1)
    # Sum: 10
    assert sugar_core.run_median(mat) == pytest.approx(10.0)

def test_median_constant():
    """3. Константы."""
    mat = np.full((3, 3), 7.0)
    assert sugar_core.run_median(mat) == pytest.approx(21.0)

def test_median_unsorted():
    """4. Неотсортированный столбец (Квадратная матрица)."""
    # J0: [100, 1, 50]. Сортируем: 1, 50, 100. Медиана 50 (R2).
    # Остальные столбцы нули, чтобы не влиять на выбор первого шага.
    mat = np.array([
        [100, 0, 0], 
        [1,   0, 0], 
        [50,  0, 0]
    ])
    assert sugar_core.run_median(mat) == pytest.approx(50.0)

def test_median_zeros():
    """5. Нули."""
    assert sugar_core.run_median(np.zeros((5,5))) == 0.0

def test_median_last_step():
    """6. 2x2 матрица."""
    mat = np.array([
        [10, 10],
        [20, 20]
    ])
    # J0: [10, 20] -> Med 20 (R1)
    # J1: [10] -> Med 10 (R0)
    # Sum: 30
    assert sugar_core.run_median(mat) == pytest.approx(30.0)


# --- 6. ТЕСТЫ КОМБИНИРОВАННЫХ АЛГОРИТМОВ (GREEDY-THRIFTY / THRIFTY-GREEDY) ---

def test_gt_switch_logic():
    """1. Жадный-Бережливый, переключение (v=2)."""
    # v=2. Первые 2 (0, 1) - Жадные. Остальные - Бережливые.
    mat = np.array([
        [100, 1,   1, 1],
        [1,   100, 1, 1],
        [1,   1,   5, 1],
        [1,   1,   50, 50]
    ])
    # J0(G): 100 (R0)
    # J1(G): 100 (R1)
    # J2(T): Остались 5(R2), 50(R3). Min 5 (R2).
    # J3(T): 50 (R3)
    # Sum: 255
    assert sugar_core.run_greedy_thrifty(mat, 2) == pytest.approx(255.0)

def test_gt_v_zero():
    """2. v=0 -> Всегда Бережливый."""
    mat = np.array([
        [10, 100],
        [50, 50]
    ])
    # J0(T): 10 (R0)
    # J1(T): 50 (R1)
    # Sum: 60
    assert sugar_core.run_greedy_thrifty(mat, 0) == pytest.approx(60.0)

def test_gt_v_one():
    """3. v=1 -> Только первый шаг Жадный."""
    mat = np.array([
        [10, 10],
        [5, 5]
    ])
    # J0(G): 10 (R0)
    # J1(T): 5 (R1)
    # Sum: 15
    assert sugar_core.run_greedy_thrifty(mat, 1) == pytest.approx(15.0)

def test_tg_switch_logic():
    """4. Бережливо-Жадный, переключение (v=2)."""
    # v=2. Первые 2 (0, 1) - Бережливые. Остальные - Жадные.
    mat = np.array([
        [1,   100, 1, 1],
        [100, 1,   1, 1],
        [50,  50,  50, 1],
        [5,   5,   5,  5]
    ])
    # J0(T): 1 (R0)
    # J1(T): 1 (R1)
    # J2(G): Остались 50(R2), 5(R3). Max 50 (R2).
    # J3(G): 5 (R3)
    # Sum: 57
    assert sugar_core.run_thrifty_greedy(mat, 2) == pytest.approx(57.0)

def test_tg_v_large():
    """5. v > n -> Всегда Бережливый."""
    mat = np.array([[10, 100], [20, 200]])
    # v=10.
    # J0(T): 10 (R0)
    # J1(T): 200 (R1)
    # Sum: 210
    assert sugar_core.run_thrifty_greedy(mat, 10) == pytest.approx(210.0)

def test_tg_zeros():
    """6. Нули для смешанного алгоритма."""
    assert sugar_core.run_thrifty_greedy(np.zeros((4,4)), 2) == 0.0