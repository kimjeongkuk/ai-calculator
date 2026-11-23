import json
import time

import re

def normalize_label(label):
    """라벨 정규화: '+', 'cross' -> 'Cross', 'x' -> 'X'"""
    if not label:
        return "UNDECIDED"
    lower_l = str(label).strip().lower()
    if lower_l in ["+", "cross"]:
        return "Cross"
    elif lower_l in ["x", "ex"]:
        return "X"
    return str(label)

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
    """크기별 MAC 연산 시간 측정 (I/O 제외, 연산 함수 구간 중심 10회 평균 ms 반환)"""
    # 더미 데이터 생성
    dummy_pattern = [[1] * n for _ in range(n)]
    dummy_filter = [[1] * n for _ in range(n)]
    
    start_time = time.perf_counter()
    for _ in range(loops):
        mac_operation(dummy_pattern, dummy_filter)
    end_time = time.perf_counter()
    
    avg_time_ms = ((end_time - start_time) * 1000.0) / loops
    return avg_time_ms

def input_matrix(size):
    """사용자로부터 size x size 행렬을 안전하게 입력받는 함수 (오류 시 재입력 유도)"""
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
            row = [float(p) for p in parts]
            matrix.append(row)
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
    
    # MAC 연산 수행
    score_a = mac_operation(pattern, filter_a)
    score_b = mac_operation(pattern, filter_b)
    
    # 성능 측정 (3x3, 10회 평균)
    avg_ms = measure_performance(3, 10)
    
    print("\n#----------------------------------------")
    print("# [3] MAC 결과")
    print("#----------------------------------------")
    print(f"A 점수: {score_a}")
    print(f"B 점수: {score_b}")
    print(f"연산 시간(평균/10회): {avg_ms:.3f} ms")
    
    # 판정 (epsilon 기준 1e-9 적용)
    epsilon = 1e-9
    if abs(score_a - score_b) < epsilon:
        print("판정: 판정 불가 (동점: |A-B| < 1e-9)")
    elif score_a > score_b:
        print("판정: 필터 A (Cross 등)")
    else:
        print("판정: 필터 B (X 등)")

def _get_ci(d, name):
    """딕셔너리에서 대소문자 무시하고 키 찾기"""
    if not isinstance(d, dict):
        return None
    for k, v in d.items():
        if str(k).strip().lower() == name:
            return v
    return None

def _extract_size(key):
    """'size_5', '5', '5x5' 등에서 첫 숫자를 크기로 추출"""
    m = re.search(r"\d+", str(key))
    return int(m.group()) if m else None

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

    filters_raw = _get_ci(data, "filters") or {}
    patterns_raw = _get_ci(data, "patterns") or {}

    # 필터 로드: 크기(int) -> {"Cross": mat, "X": mat}
    loaded_filters = {}
    for f_key, f_data in filters_raw.items():
        size = _extract_size(f_key)
        if size is None or not isinstance(f_data, dict):
            continue
        loaded_filters[size] = {normalize_label(k): v for k, v in f_data.items()}
        print(f"✓ {str(f_key):<8} 필터 로드 완료 ({', '.join(loaded_filters[size].keys())})")

    # 패턴을 (키, 정보) 리스트로 통일 (dict / list 모두 지원)
    if isinstance(patterns_raw, dict):
        pattern_items = list(patterns_raw.items())
    elif isinstance(patterns_raw, list):
        pattern_items = [
            (str(p.get("id") or p.get("name") or f"pattern_{i+1}"), p)
            for i, p in enumerate(patterns_raw) if isinstance(p, dict)
        ]
    else:
        pattern_items = []

    # 테스트가 0개면 성공으로 처리하지 않고 원인 안내
    if not pattern_items or not loaded_filters:
        print("\n오류: 분석할 데이터를 읽지 못했습니다.")
        print(f"- 최상위 키: {list(data.keys()) if isinstance(data, dict) else type(data).__name__}")
        print(f"- 로드된 필터 수: {len(loaded_filters)}, 패턴 수: {len(pattern_items)}")
        print("data.json의 'filters' / 'patterns' 구조를 확인해주세요.")
        return

    print("\n#----------------------------------------")
    print("# [2] 패턴 분석 (라벨 정규화 적용)")
    print("#----------------------------------------")

    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    failure_records = []
    epsilon = 1e-9

    for p_key, p_info in pattern_items:
        total_tests += 1
        pattern_mat = (p_info.get("input") or p_info.get("pattern")
                       or p_info.get("matrix"))
        raw_expected = p_info.get("expected", p_info.get("label"))
        expected = normalize_label(raw_expected)

        print(f"--- {p_key} ---")

        def fail(reason):
            nonlocal failed_tests
            failed_tests += 1
            failure_records.append((p_key, reason))
            print(f"판정: FAIL | 사유: {reason}")

        if not pattern_mat:
            fail("패턴 데이터 누락")
            continue

        size = len(pattern_mat)
        target = loaded_filters.get(size, {})
        cross_filter = target.get("Cross")
        x_filter = target.get("X")

        if not cross_filter or not x_filter:
            fail(f"{size}x{size} 필터 데이터 누락")
            continue
        if any(len(row) != size for row in pattern_mat) or \
           len(cross_filter) != size or len(x_filter) != size:
            fail("크기 불일치")
            continue

        score_cross = mac_operation(pattern_mat, cross_filter)
        score_x = mac_operation(pattern_mat, x_filter)

        if abs(score_cross - score_x) < epsilon:
            pred = "UNDECIDED"
        elif score_cross > score_x:
            pred = "Cross"
        else:
            pred = "X"

        print(f"Cross 점수: {score_cross}")
        print(f"X 점수: {score_x}")

        if pred == "UNDECIDED":
            passed_str = "FAIL (동점 UNDECIDED)"
            failed_tests += 1
            failure_records.append((p_key, "동점(UNDECIDED) 처리 규칙에 따라 FAIL"))
        elif pred == expected:
            passed_str = "PASS"
            passed_tests += 1
        else:
            passed_str = f"FAIL (예측 {pred} != 기대 {expected})"
            failed_tests += 1
            failure_records.append((p_key, f"예측값({pred})과 기대값({expected}) 불일치"))
        print(f"판정: {pred} | expected: {expected} | {passed_str}")

    print("\n#----------------------------------------")
    print("# [3] 성능 분석 (평균/10회)")
    print("#----------------------------------------")
    print(f"{'크기':<10} {'평균 시간(ms)':<15} {'연산 횟수'}")
    print("-" * 40)
    for s in [3, 5, 13, 25]:
        t = measure_performance(s, 10)
        print(f"{str(s)+'x'+str(s):<10} {t:<15.3f} {s*s}")

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
    else:
        print("\n모든 테스트 케이스가 성공했습니다!")

def main():
    while True:
        print("\n=== Mini NPU Simulator ===")
        print("[모드 선택]")
        print("1. 사용자 입력 (3x3)")
        print("2. data.json 분석")
        print("3. 프로그램 종료")
        choice = input("선택: ").strip()
        
        if choice == "1":
            mode_1_user_input()
        elif choice == "2":
            mode_2_json_analysis()
        elif choice == "3":
            print("프로그램을 종료합니다.")
            break
        else:
            print("잘못된 입력입니다. 1, 2, 3 중에서 선택해주세요.")

if __name__ == "__main__":
    main()