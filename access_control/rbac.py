import json
from pathlib import Path
 
BASE_DIR = Path(__file__).resolve().parent.parent
ROLES_FILE = BASE_DIR / "config" / "roles.json"
USER_ROLES_FILE = BASE_DIR / "config" / "user_roles.json"
 
 
def _load_roles():
    with open(ROLES_FILE, "r", encoding="utf-8") as file:
        return json.load(file)
 
 
def _load_user_roles():
    with open(USER_ROLES_FILE, "r", encoding="utf-8") as file:
        return json.load(file)
 
 
def _save_user_roles(user_roles):
    with open(USER_ROLES_FILE, "w", encoding="utf-8") as file:
        json.dump(user_roles, file, ensure_ascii=False, indent=4)
 
 
# 사용자에게 부여된 역할(부서) 조회
def get_user_role(username):
    user_roles = _load_user_roles()
    return user_roles.get(username)
 
 
# 특정 사용자가 시스템에 대한 권한을 가지고 있는지 확인 (역할 매트릭스 기준)
def has_permission(username, system, requested_permission):
    from policy import check_policy  # 정책 매트릭스 재사용
 
    department = get_user_role(username)
    if department is None:
        return False
 
    return check_policy(department, system, requested_permission)
 
 
# 사용자에게 역할(부서) 부여
def assign_role(username, role):
    roles_data = _load_roles()
    valid_roles = [item["role"] for item in roles_data["roles"]]
 
    if role not in valid_roles:
        return False, f"존재하지 않는 역할입니다: {role}"
 
    user_roles = _load_user_roles()
    user_roles[username] = role
    _save_user_roles(user_roles)
    return True, f"'{username}'에게 '{role}' 역할을 부여했습니다."
 
 
# 사용자의 역할 회수
def revoke_role(username):
    user_roles = _load_user_roles()
 
    if username not in user_roles:
        return False, f"'{username}'에게 부여된 역할이 없습니다."
 
    del user_roles[username]
    _save_user_roles(user_roles)
    return True, f"'{username}'의 역할을 회수했습니다."
 
 
if __name__ == "__main__":
    print(assign_role("choi2", "운영팀"))
    print(has_permission("choi2", "운영 시스템", "관리자"))
    print(revoke_role("choi2"))
    print(has_permission("choi2", "운영 시스템", "관리자"))