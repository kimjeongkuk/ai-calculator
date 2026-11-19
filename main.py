import json
import time

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

    filters_raw = data.get("filters", {})
    patterns_raw = data.get("patterns", {})
    
    loaded_filters = {}
    for f_key, f_data in filters_raw.items():
        # f_key 예: "size_5", "size_13", "size_25"
        loaded_filters[f_key] = {}
        for sub_k, sub_mat in f_data.items():
            std_sub_k = normalize_label(sub_k)
            loaded_filters[f_key][std_sub_k] = sub_mat
        print(f"✓ {f_key:<8} 필터 로드 완료 (Cross, X)")

    print("\n#----------------------------------------")
    print("# [2] 패턴 분석 (라벨 정규화 적용)")
    print("#----------------------------------------")
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    failure_records = []
    
    epsilon = 1e-9

    for p_key, p_info in patterns_raw.items():
        total_tests += 1
        pattern_mat = p_info.get("input")
        raw_expected = p_info.get("expected")
        expected = normalize_label(raw_expected)
        
        # 키에서 크기 추출 (예: size_5_1 -> size_5)
        parts = p_key.split("_")
        if len(parts) >= 2:
            size_str = f"size_{parts[1]}"
        else:
            size_str = "size_5"
            
        target_filters = loaded_filters.get(size_str, {})
        cross_filter = target_filters.get("Cross")
        x_filter = target_filters.get("X")
        
        # 스키마 및 크기 검증
        if not cross_filter or not x_filter or not pattern_mat:
            failed_tests += 1
            reason = "스키마 불일치 또는 필터 데이터 누락"
            failure_records.append((p_key, reason))
            print(f"--- {p_key} ---")
            print(f"판정: FAIL | 사유: {reason}")
            continue
            
        # 크기 일치 검증
        p_rows = len(pattern_mat)
        f_rows = len(cross_filter)
        if p_rows != f_rows:
            failed_tests += 1
            reason = f"크기 불일치 (패턴 행:{p_rows} != 필터 행:{f_rows})"
            failure_records.append((p_key, reason))
            print(f"--- {p_key} ---")
            print(f"판정: FAIL | 사유: {reason}")
            continue

        # MAC 연산 수행
        score_cross = mac_operation(pattern_mat, cross_filter)
        score_x = mac_operation(pattern_mat, x_filter)
        
        # 판정 결정
        if abs(score_cross - score_x) < epsilon:
            pred = "UNDECIDED"
        elif score_cross > score_x:
            pred = "Cross"
        else:
            pred = "X"
            
        # PASS/FAIL 비교 판단
        if pred == "UNDECIDED":
            is_pass = False
            reason = "동점(UNDECIDED) 처리 규칙에 따라 FAIL"
        elif pred == expected:
            is_pass = True
            reason = "정상 통과"
        else:
            is_pass = False
            reason = f"예측값({pred})과 기대값({expected}) 불일치"
            
        if is_pass:
            passed_tests += 1
            status_str = "PASS"
        else:
            failed_tests += 1
            status_str = f"FAIL ({reason})"
            failure_records.append((p_key, reason))
            
        print(f"--- {p_key} ---")
        print(f"Cross 점수: {score_cross}")
        print(f"X 점수: {score_x}")
        print(f"판정: {pred} | expected: {expected} | {status_str}")

    print("\n#----------------------------------------")
    print("# [3] 성능 분석 (평균/10회)")
    print("#----------------------------------------")
    sizes_to_test = [3, 5, 13, 25]
    perf_results = []
    for s in sizes_to_test:
        avg_t = measure_performance(s, 10)
        ops_count = s * s
        perf_results.append((s, avg_t, ops_count))
        
    print(f"{'크기':<10} {'평균 시간(ms)':<15} {'연산 횟수'}")
    print("-" * 40)
    for s, t, ops in perf_results:
        print(f"{s}×{s:<8} {t:<15.3f} {ops}")

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