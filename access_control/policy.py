import json
from pathlib import Path
from datetime import datetime
 
# 정책 파일 불러오기
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / "config" / "policy.json"
 
with open(CONFIG_FILE, "r", encoding="utf-8") as file:
    policy_data = json.load(file)
 
# 정책권한과 예외처리 저장
policy = policy_data["policy"]
exceptions = policy_data["exceptions"]
 
# 권한 수준 정의
permission_level = {
    "없음": 0,
    "조회": 1,
    "수정": 2,
    "관리자": 3
}
 
 
# 일반 권한 정책 검사
def check_policy(department, system, requested_permission):
    if department not in policy:
        return False
    department_policy = policy[department]
 
    if system not in department_policy:
        return False
 
    allowed_permission = department_policy[system]
 
    allowed_level = permission_level.get(allowed_permission, 0)
    requested_level = permission_level.get(requested_permission, 0)
 
    if requested_level == 0:
        return False
 
    if requested_level <= allowed_level:
        return True
 
    return False
 
 
# 예외처리 유효성 검사
def is_exception_valid(username, system, permission):
    now = datetime.now()
 
    for exception in exceptions:
        if exception["username"] != username:
            continue
 
        if exception["system"] != system:
            continue
 
        if exception["permission"] != permission:
            continue
 
        expires_at = datetime.strptime(exception["expires_at"], "%Y-%m-%d %H:%M")
 
        if now <= expires_at:
            return True
    return False
 
 
# 통합 판단 함수: RBAC 역할 조회 + 정책 검사 + 예외 검사를 한 번에 수행
def evaluate_access(username, system, requested_permission):
    import rbac  # 사용자 -> 부서(역할) 조회용
 
    department = rbac.get_user_role(username)
 
    if department is None:
        return {
            "username": username,
            "department": None,
            "system": system,
            "requested_permission": requested_permission,
            "allowed": False,
            "reason": "등록되지 않은 사용자입니다."
        }
 
    if check_policy(department, system, requested_permission):
        return {
            "username": username,
            "department": department,
            "system": system,
            "requested_permission": requested_permission,
            "allowed": True,
            "reason": "정책상 허용된 권한입니다."
        }
 
    if is_exception_valid(username, system, requested_permission):
        return {
            "username": username,
            "department": department,
            "system": system,
            "requested_permission": requested_permission,
            "allowed": True,
            "reason": "유효한 예외 승인으로 허용되었습니다."
        }
 
    return {
        "username": username,
        "department": department,
        "system": system,
        "requested_permission": requested_permission,
        "allowed": False,
        "reason": "정책 위반이며 유효한 예외 승인도 없습니다."
    }
 
 
if __name__ == "__main__":
    # 간단한 동작 확인용 (직접 실행했을 때만 동작)
    print(check_policy("개발팀", "개발 시스템", "조회"))
    print(is_exception_valid("kim", "운영 시스템", "관리자"))
    print(evaluate_access("kim", "개발 시스템", "조회"))