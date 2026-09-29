import json
from pathlib import Path
from datetime import datetime
 
BASE_DIR = Path(__file__).resolve().parent.parent
REQUESTS_FILE = BASE_DIR / "access_control" / "requests.json"
SLA_CONFIG_FILE = BASE_DIR / "config" / "sla_config.json"
 
 
# ---------- 파일 입출력 ----------
 
def _load_requests():
    with open(REQUESTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
 
 
def _save_requests(requests):
    with open(REQUESTS_FILE, "w", encoding="utf-8") as f:
        json.dump(requests, f, ensure_ascii=False, indent=4)
 
 
def _load_sla_config():
    with open(SLA_CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
 
 
# ---------- 요청 생성 ----------
 
def create_request(user, department, system, permission_level, approver):
    requests = _load_requests()
 
    # ① 새 request_id 생성 (REQ-001, REQ-002 ... 형태로 자동 채번)
    new_number = len(requests) + 1
    new_id = f"REQ-{new_number:03d}"
 
    # ② config에서 시스템별 SLA 기준시간 조회 (없으면 default 사용)
    sla_config = _load_sla_config()
    sla_hours = sla_config["system_sla_hours"].get(system, sla_config["default_sla_hours"])
 
    # ③ 요청 생성 (상태는 무조건 "검토중"으로 시작)
    new_request = {
        "request_id": new_id,
        "user": user,
        "department": department,
        "system": system,
        "permission_level": permission_level,
        "status": "검토중",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "approver": approver,
        "sla_hours": sla_hours
    }
 
    requests.append(new_request)
    _save_requests(requests)
    return new_request
 
 
# ---------- 승인 / 반려 ----------
 
def approve_request(request_id):
    import policy  # 1일차 정책 검증(evaluate_access) 재사용
 
    requests = _load_requests()
 
    for req in requests:
        if req["request_id"] == request_id:
            if req["status"] != "검토중":
                return False, f"{request_id}는 이미 처리된 요청입니다 (현재 상태: {req['status']})"
 
            # 이중 검증: RBAC 정책 + 예외 승인까지 확인
            access_result = policy.evaluate_access(
                req["user"], req["system"], req["permission_level"]
            )
 
            if not access_result["allowed"]:
                req["status"] = "반려"
                _save_requests(requests)
                return False, f"{request_id} 자동 반려 - {access_result['reason']}"
 
            req["status"] = "승인"
            _save_requests(requests)
            return True, f"{request_id} 승인 완료 - {access_result['reason']}"
 
    return False, f"{request_id}를 찾을 수 없습니다"
 
 
def reject_request(request_id):
    requests = _load_requests()
 
    for req in requests:
        if req["request_id"] == request_id:
            if req["status"] != "검토중":
                return False, f"{request_id}는 이미 처리된 요청입니다 (현재 상태: {req['status']})"
 
            req["status"] = "반려"
            _save_requests(requests)
            return True, f"{request_id} 반려 완료"
 
    return False, f"{request_id}를 찾을 수 없습니다"
 
 
# ---------- SLA 초과 감지 ----------
 
def check_sla_breach(request):
    if request["status"] != "검토중":
        return False
 
    created_at = datetime.strptime(request["created_at"], "%Y-%m-%d %H:%M")
    now = datetime.now()
 
    elapsed_hours = (now - created_at).total_seconds() / 3600
    return elapsed_hours > request["sla_hours"]
 
 
def check_and_alert_sla_breaches():
    requests = _load_requests()
    breached = [req for req in requests if check_sla_breach(req)]
 
    if not breached:
        print("SLA 위반 요청 없음")
        return breached
 
    print("=" * 50)
    print(f"[SLA 경고] SLA 초과 요청 감지: {len(breached)}건")
    print("=" * 50)
 
    for req in breached:
        created_at = datetime.strptime(req["created_at"], "%Y-%m-%d %H:%M")
        elapsed_hours = (datetime.now() - created_at).total_seconds() / 3600
        print(
            f"  [{req['request_id']}] {req['user']} / {req['system']} / "
            f"{req['permission_level']} -> 기준 {req['sla_hours']}시간, "
            f"경과 {elapsed_hours:.1f}시간 초과!"
        )
 
    print("=" * 50)
    return breached
 
 
# ---------- 직접 실행 시 동작 확인 ----------
 
if __name__ == "__main__":
    print("--- 전체 요청 SLA 상태 ---")
    for req in _load_requests():
        print(f"{req['request_id']} ({req['status']}) - SLA 초과: {check_sla_breach(req)}")
 
    print("\n--- SLA 초과 알림 ---")
    check_and_alert_sla_breaches()
 
    print("\n--- 승인/반려 테스트 ---")
    print(approve_request("REQ-001"))
    print(approve_request("REQ-004"))