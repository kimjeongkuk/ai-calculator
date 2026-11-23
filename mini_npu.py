import json
import re
import time

EPSILON = 1e-9


def normalize_label(label):
    """라벨 정규화: '+', 'cross' -> 'Cross', 'x' -> 'X'"""
    if label is None or str(label).strip() == "":
        return "UNDECIDED"
    lower_l = str(label).strip().lower()
    if lower_l in ["+", "cross"]:
        return "Cross"
    if lower_l in ["x", "ex"]:
        return "X"
    return str(label).strip()


def matrix_size(mat):
    """유효한 정사각 숫자 행렬이면 크기(n)를, 아니면 None을 반환"""
    if not isinstance(mat, list) or not mat:
        return None
    n = len(mat)
    for row in mat:
        if not isinstance(row, list) or len(row) != n:
            return None
        for v in row:
            if isinstance(v, bool):
                return None
            try:
                float(v)
            except (TypeError, ValueError):
                return None
    return n


def mac_operation(pattern, filter_mat):
    """외부 라이브러리 없이 순수 반복문으로 구현한 MAC 연산"""
    rows = len(pattern)
    cols = len(pattern[0])
    score = 0.0
    for r in range(rows):
        for c in range(cols):
            score += float(pattern[r][c]) * float(filter_mat[r][c])
    return score


def measure_performance(n, loops=10):
    """크기별 MAC 연산 시간 측정 (I/O 제외, loops회 평균 ms 반환)"""
    dummy_pattern = [[1] * n for _ in range(n)]
    dummy_filter = [[1] * n for _ in range(n)]

    start_time = time.perf_counter()
    for _ in range(loops):
        mac_operation(dummy_pattern, dummy_filter)
    end_time = time.perf_counter()

    return ((end_time - start_time) * 1000.0) / loops


def input_matrix(size):
    """size x size 행렬을 안전하게 입력받는 함수 (오류 시 해당 줄 재입력)"""
    print(f"({size}줄 입력, 각 줄에 숫자 {size}개를 공백으로 구분해 입력)")
    matrix = []
    while len(matrix) < size:
        line_num = len(matrix) + 1
        raw = input(f"줄 {line_num}: ").strip()
        parts = raw.split()
        if len(parts) != size:
            print(f"입력 형식 오류: 각 줄에 정확히 {size}개의 숫자를 공백으로 구분해 입력하세요.")
            continue
        try:
            matrix.append([float(p) for p in parts])
        except ValueError:
            print("입력 형식 오류: 숫자만 입력할 수 있습니다. 다시 입력해주세요.")
    return matrix


def mode_1_user_input():
    print("\n#----------------------------------------")
    print("# [1] 필터 입력 (3x3)")
    print("#----------------------------------------")
    print("필터 A 입력:")
    filter_a = input_matrix(3)

    print("\n필터 B 입력:")
    filter_b = input_matrix(3)

    print("\n#----------------------------------------")
    print("# [2] 패턴 입력 (3x3)")
    print("#----------------------------------------")
    pattern = input_matrix(3)

    score_a = mac_operation(pattern, filter_a)
    score_b = mac_operation(pattern, filter_b)
    avg_ms = measure_performance(3, 10)

    print("\n#----------------------------------------")
    print("# [3] MAC 결과")
    print("#----------------------------------------")
    print(f"A 점수: {score_a}")
    print(f"B 점수: {score_b}")
    print(f"연산 시간(평균/10회): {avg_ms:.3f} ms")

    if abs(score_a - score_b) < EPSILON:
        print("판정: 판정 불가 (동점: |A-B| < 1e-9)")
    elif score_a > score_b:
        print("판정: 필터 A")
    else:
        print("판정: 필터 B")


def load_filters(filters_raw):
    """filters 항목을 라벨 정규화하여 {size_key: {'Cross': mat, 'X': mat}} 로 변환"""
    loaded = {}
    for f_key, f_data in filters_raw.items():
        if not isinstance(f_data, dict):
            print(f"✗ {f_key:<8} 필터 형식 오류 (건너뜀)")
            continue
        loaded[f_key] = {}
        for sub_k, sub_mat in f_data.items():
            loaded[f_key][normalize_label(sub_k)] = sub_mat

        ok = all(
            matrix_size(loaded[f_key].get(name)) is not None
            for name in ("Cross", "X")
        )
        if ok:
            print(f"✓ {f_key:<8} 필터 로드 완료 (Cross, X)")
        else:
            print(f"✗ {f_key:<8} 필터 누락 또는 형식 오류 (Cross/X 정사각 행렬 필요)")
    return loaded


def find_size_key(p_key, pattern_mat):
    """패턴 키(size_5_1 등)에서 크기 키를 추출, 실패하면 패턴 크기로 추정"""
    m = re.match(r"^size_(\d+)", str(p_key))
    if m:
        return f"size_{m.group(1)}"
    n = matrix_size(pattern_mat)
    return f"size_{n}" if n else None


def mode_2_json_analysis():
    print("\n#----------------------------------------")
    print("# [1] 필터 로드")
    print("#----------------------------------------")
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("오류: data.json 파일을 찾을 수 없습니다. 파일을 같은 디렉토리에 위치시켜 주세요.")
        return
    except json.JSONDecodeError as e:
        print(f"오류: data.json 형식이 올바르지 않습니다. ({e})")
        return

    if not isinstance(data, dict):
        print("오류: data.json 최상위 구조가 올바르지 않습니다.")
        return

    loaded_filters = load_filters(data.get("filters", {}))
    patterns_raw = data.get("patterns", {})

    print("\n#----------------------------------------")
    print("# [2] 패턴 분석 (라벨 정규화 적용)")
    print("#----------------------------------------")

    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    failure_records = []

    for p_key, p_info in patterns_raw.items():
        total_tests += 1
        print(f"--- {p_key} ---")

        def fail(reason):
            nonlocal failed_tests
            failed_tests += 1
            failure_records.append((p_key, reason))
            print(f"판정: FAIL | 사유: {reason}")

        if not isinstance(p_info, dict):
            fail("스키마 불일치 (패턴 항목이 객체가 아님)")
            continue

        pattern_mat = p_info.get("input")
        expected = normalize_label(p_info.get("expected"))

        p_size = matrix_size(pattern_mat)
        if p_size is None:
            fail("스키마 불일치 (패턴이 올바른 정사각 숫자 행렬이 아님)")
            continue

        size_key = find_size_key(p_key, pattern_mat)
        target_filters = loaded_filters.get(size_key, {})
        cross_filter = target_filters.get("Cross")
        x_filter = target_filters.get("X")

        if cross_filter is None or x_filter is None:
            fail(f"필터 데이터 누락 ({size_key})")
            continue

        c_size = matrix_size(cross_filter)
        x_size = matrix_size(x_filter)
        if c_size is None or x_size is None:
            fail("필터 형식 오류 (정사각 숫자 행렬이 아님)")
            continue
        if not (p_size == c_size == x_size):
            fail(f"크기 불일치 (패턴:{p_size}, Cross:{c_size}, X:{x_size})")
            continue

        if expected not in ("Cross", "X"):
            fail(f"expected 라벨 오류 ({p_info.get('expected')!r})")
            continue

        score_cross = mac_operation(pattern_mat, cross_filter)
        score_x = mac_operation(pattern_mat, x_filter)

        if abs(score_cross - score_x) < EPSILON:
            pred = "UNDECIDED"
        elif score_cross > score_x:
            pred = "Cross"
        else:
            pred = "X"

        print(f"Cross 점수: {score_cross}")
        print(f"X 점수: {score_x}")

        if pred == "UNDECIDED":
            status = "FAIL (동점 UNDECIDED 처리 규칙)"
            ok = False
            reason = "동점(UNDECIDED) 처리 규칙에 따라 FAIL"
        elif pred == expected:
            status = "PASS"
            ok = True
        else:
            reason = f"예측값({pred})과 기대값({expected}) 불일치"
            status = f"FAIL ({reason})"
            ok = False

        if ok:
            passed_tests += 1
        else:
            failed_tests += 1
            failure_records.append((p_key, reason))
        print(f"판정: {pred} | expected: {expected} | {status}")

    print("\n#----------------------------------------")
    print("# [3] 성능 분석 (평균/10회)")
    print("#----------------------------------------")
    print(f"{'크기':<10} {'평균 시간(ms)':<15} {'연산 횟수'}")
    print("-" * 40)
    for s in [3, 5, 13, 25]:
        avg_t = measure_performance(s, 10)
        print(f"{f'{s}x{s}':<10} {avg_t:<15.3f} {s * s}")

    print("\n#----------------------------------------")
    print("# [4] 결과 요약")
    print("#----------------------------------------")
    print(f"총 테스트: {total_tests}개")
    print(f"통과: {passed_tests}개")
    print(f"실패: {failed_tests}개")

    if failure_records:
        print("\n실패 케이스:")
        for k, r in failure_records:
            print(f"- {k}: {r}")
    elif total_tests > 0:
        print("\n모든 테스트 케이스가 성공했습니다!")


def main():
    while True:
        print("\n=== Mini NPU Simulator ===")
        print("[모드 선택]")
        print("1. 사용자 입력 (3x3)")
        print("2. data.json 분석")
        print("3. 프로그램 종료")
        try:
            choice = input("선택: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n프로그램을 종료합니다.")
            break

        try:
            if choice == "1":
                mode_1_user_input()
            elif choice == "2":
                mode_2_json_analysis()
            elif choice == "3":
                print("프로그램을 종료합니다.")
                break
            else:
                print("잘못된 입력입니다. 1, 2, 3 중에서 선택해주세요.")
        except (EOFError, KeyboardInterrupt):
            print("\n입력이 중단되어 메뉴로 돌아갑니다.")


if __name__ == "__main__":
    main()
