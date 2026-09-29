"""
권한 회수(Revoke) 처리 스크립트

- classify_revoke_target(): 과다권한 후보의 사유/권한수준에 따라 처리 방식을 분류
- run_revocation(): 과다권한 후보 목록을 순회하며 회수 처리를 수행하고 회수 이력을 생성
- save_revoke_logs(): 회수 이력을 revoke_logs_YYYYMMDD.json 으로 저장

입력: overprivilege.generate_overprivilege_report() 의 candidates
"""

import json
import os
from datetime import datetime


# ---------------------------------------------------------------------------
# 1. 회수 방식 분류
# ---------------------------------------------------------------------------
def classify_revoke_target(candidate):
    """
    candidate: {"username":..., "type": "미사용 권한" | "부서 불일치", "reason":..., ...}
    반환값: "즉시 회수" | "승인 필요" | "즉시 알림 후 유예 회수"
    """
    reason = candidate.get("reason", "")

    if "퇴사" in reason:
        return "즉시 회수"

    if candidate.get("type") == "부서 불일치":
        return "승인 필요"

    return "즉시 알림 후 유예 회수"


# ---------------------------------------------------------------------------
# 2. 회수 처리 및 이력 생성
# ---------------------------------------------------------------------------
def run_revocation(candidates, today=None):
    """
    candidates: overprivilege 리포트의 candidates 리스트
    반환값: revoke_logs 리스트
    """
    today = today or datetime.now()
    revoke_logs = []

    for candidate in candidates or []:
        username = candidate.get("username")
        permission = candidate.get("permission", candidate.get("system", "부서권한"))
        action = classify_revoke_target(candidate)

        if action == "즉시 회수":
            status = "회수 완료"
        elif action == "승인 필요":
            status = "승인 대기"
        else:
            status = "회수 예정 알림"

        revoke_logs.append({
            "username": username,
            "permission": permission,
            "type": candidate.get("type"),
            "action": action,
            "status": status,
            "reason": candidate.get("reason"),
            "processed_at": today.strftime("%Y-%m-%d %H:%M")
        })

    return revoke_logs


# ---------------------------------------------------------------------------
# 3. 회수 이력 저장
# ---------------------------------------------------------------------------
def save_revoke_logs(revoke_logs, output_dir=".", today=None):
    today = today or datetime.now()
    filename = f"revoke_logs_{today.strftime('%Y%m%d')}.json"
    path = os.path.join(output_dir, filename)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(revoke_logs, f, ensure_ascii=False, indent=2)

    return path


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))

    with open(os.path.join(base_dir, "overprivilege_report_20260923.json"), encoding="utf-8") as f:
        report = json.load(f)

    logs = run_revocation(report.get("candidates", []))
    for log in logs:
        print(log)

    saved_path = save_revoke_logs(logs, output_dir=base_dir)
    print(f"\n회수 이력 저장 완료: {saved_path}")
