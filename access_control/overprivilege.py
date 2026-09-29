
"""
과다권한(Overprivilege) 탐지 스크립트
 
- detect_unused_permissions(): 90일(기본값) 이상 사용되지 않은 권한을 탐지
- detect_dept_mismatch(): 권한 부여 당시 부서와 현재 부서가 다른 사용자를 탐지
- generate_overprivilege_report(): 위 두 탐지 결과를 종합해 리포트를 만들고
  overprivilege_report_YYYYMMDD.json 으로 저장
 
입력 파일
- access_logs.json : {"permissions": {...}, "logs": [...]}
- dept_history.json : {"assigned": {...}, "current": {...}}
"""
 
import json
import os
from datetime import datetime, timedelta
 
 
# ---------------------------------------------------------------------------
# 1. 미사용 권한 탐지
# ---------------------------------------------------------------------------
def detect_unused_permissions(permissions, usage_logs, days=90, today=None):
    """
    permissions: {username: [permission, ...]}  # 사용자가 현재 보유한 권한 목록
    usage_logs: [{"username":..., "permission":..., "used_at": "YYYY-MM-DD"}, ...]
    days: 미사용 판정 기준 일수 (기본 90일)
    today: 기준 날짜(datetime). 테스트 시 고정값을 넣을 수 있도록 인자로 분리
 
    반환값: {username: [{"permission":..., "last_used": "YYYY-MM-DD" 또는 None}, ...]}
    """
    # 극단적 케이스 방어: permissions나 usage_logs가 비어 있어도 에러 없이 빈 결과를 반환해야 함
    permissions = permissions or {}
    usage_logs = usage_logs or []
 
    today = today or datetime.now()
    cutoff = today - timedelta(days=days)
 
    # (username, permission) 조합별 마지막 사용일 계산
    last_used = {}
    for log in usage_logs:
        username = log.get("username")
        permission = log.get("permission")
        used_at_raw = log.get("used_at")
        if not username or not permission or not used_at_raw:
            # 필드가 누락된 로그는 건너뛴다 (극단적 케이스 방어)
            continue
        used_at = datetime.strptime(used_at_raw, "%Y-%m-%d")
        key = (username, permission)
        if key not in last_used or used_at > last_used[key]:
            last_used[key] = used_at
 
    result = {}
    for username, perms in permissions.items():
        unused = []
        for perm in perms or []:
            key = (username, perm)
            last_date = last_used.get(key)
            # 로그가 아예 없으면(한 번도 사용 안 함) 미사용으로 간주
            if last_date is None or last_date < cutoff:
                unused.append({
                    "permission": perm,
                    "last_used": last_date.strftime("%Y-%m-%d") if last_date else None
                })
        if unused:
            result[username] = unused
 
    return result
 
 
# ---------------------------------------------------------------------------
# 2. 부서 불일치 탐지
# ---------------------------------------------------------------------------
def detect_dept_mismatch(assigned_departments, current_departments):
    """
    assigned_departments: {username: "권한 부여 당시 부서"}
    current_departments: {username: "현재 부서"}
 
    반환값: [{"username":..., "assigned_department":..., "current_department":...}, ...]
    """
    assigned_departments = assigned_departments or {}
    current_departments = current_departments or {}
 
    mismatches = []
    for username, assigned_dept in assigned_departments.items():
        current_dept = current_departments.get(username)
        # 현재 부서 정보가 없거나(예: 조직 개편 중 누락), 부서가 달라졌으면 불일치로 판정
        if current_dept is None or assigned_dept != current_dept:
            mismatches.append({
                "username": username,
                "assigned_department": assigned_dept,
                "current_department": current_dept
            })
 
    return mismatches
 
 
# ---------------------------------------------------------------------------
# 3. 종합 리포트 생성
# ---------------------------------------------------------------------------
def generate_overprivilege_report(permissions, usage_logs,
                                   assigned_departments, current_departments,
                                   days=90, today=None):
    """
    두 탐지 함수를 실행해 결과를 종합한 뒤 리포트 딕셔너리를 반환한다.
    파일 저장은 save_report()에서 별도로 처리한다.
    """
    today = today or datetime.now()
 
    unused_result = detect_unused_permissions(permissions, usage_logs, days=days, today=today)
    mismatch_result = detect_dept_mismatch(assigned_departments, current_departments)
 
    candidates = []
 
    # 미사용 권한 후보 추가
    for username, items in unused_result.items():
        for item in items:
            candidates.append({
                "username": username,
                "type": "미사용 권한",
                "permission": item["permission"],
                "last_used": item["last_used"],
                "reason": f"{days}일 이상 미사용"
            })
 
    # 부서 불일치 후보 추가
    for item in mismatch_result:
        candidates.append({
            "username": item["username"],
            "type": "부서 불일치",
            "assigned_department": item["assigned_department"],
            "current_department": item["current_department"],
            "reason": "권한 부여 당시 부서와 현재 부서가 다름"
        })
 
    report = {
        "generated_at": today.strftime("%Y-%m-%d"),
        "criteria_days": days,
        "summary": {
            "unused_permission_users": len(unused_result),
            "unused_permission_cases": sum(len(v) for v in unused_result.values()),
            "department_mismatch_cases": len(mismatch_result),
            "total_candidates": len(candidates)
        },
        "candidates": candidates
    }
 
    return report
 
 
# ---------------------------------------------------------------------------
# 4. 리포트 파일 저장
# ---------------------------------------------------------------------------
def save_report(report, output_dir=".", today=None):
    """
    리포트를 overprivilege_report_YYYYMMDD.json 으로 저장하고 저장 경로를 반환한다.
    """
    today = today or datetime.now()
    filename = f"overprivilege_report_{today.strftime('%Y%m%d')}.json"
    path = os.path.join(output_dir, filename)
 
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
 
    return path
 
 
# ---------------------------------------------------------------------------
# 실행부
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
 
    with open(os.path.join(base_dir, "access_logs.json"), encoding="utf-8") as f:
        access_data = json.load(f)
 
    with open(os.path.join(base_dir, "dept_history.json"), encoding="utf-8") as f:
        dept_data = json.load(f)
 
    report = generate_overprivilege_report(
        permissions=access_data.get("permissions", {}),
        usage_logs=access_data.get("logs", []),
        assigned_departments=dept_data.get("assigned", {}),
        current_departments=dept_data.get("current", {})
    )
 
    if report["summary"]["total_candidates"] == 0:
        print("과다권한 후보가 없습니다.")
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
 
    saved_path = save_report(report, output_dir=base_dir)
    print(f"\n리포트 저장 완료: {saved_path}")