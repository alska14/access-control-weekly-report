"""
접근통제 주간 리포트 자동화 스크립트

generate_weekly_report() 는 1~4일차에서 만든 5개 모듈의 결과를 통합한다.
    1. RBAC 상태      - rbac.py  (roles.json, user_roles.json)
    2. 정책 위반      - policy.py (requests.json 중 '반려' 처리된 건의 사유)
    3. 요청 처리 현황 - requests_flow.py (requests.json + SLA 초과 여부)
    4. 과다권한       - overprivilege.py (access_logs.json, dept_history.json)
    5. 회수 이력      - revoke.py (4번 결과 기반 회수 처리)

save_weekly_report_md() 는 위 리포트를 access_control_weekly_report_YYYYMMDD.md 로 저장한다.
"""

import json
import os
from datetime import datetime

import policy
import rbac
import requests_flow
import overprivilege
import revoke

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)


# ---------------------------------------------------------------------------
# 1. RBAC 상태
# ---------------------------------------------------------------------------
def collect_rbac_status():
    roles_data = rbac._load_roles()
    user_roles = rbac._load_user_roles()

    valid_roles = [item["role"] for item in roles_data["roles"]]

    return {
        "total_roles": len(valid_roles),
        "roles": valid_roles,
        "total_users": len(user_roles),
        "user_roles": user_roles
    }


# ---------------------------------------------------------------------------
# 2. 정책 위반 + 3. 요청 처리 현황 (requests.json 공통 사용)
# ---------------------------------------------------------------------------
def collect_request_status():
    requests_data = requests_flow._load_requests()

    status_count = {}
    sla_breaches = []
    policy_violations = []

    for req in requests_data:
        status_count[req["status"]] = status_count.get(req["status"], 0) + 1

        if requests_flow.check_sla_breach(req):
            sla_breaches.append(req["request_id"])

        # 정책 위반: RBAC/정책 기준으로 재검사했을 때 허용되지 않는 요청
        access_result = policy.evaluate_access(
            req["user"], req["system"], req["permission_level"]
        )
        if not access_result["allowed"]:
            policy_violations.append({
                "request_id": req["request_id"],
                "user": req["user"],
                "system": req["system"],
                "permission_level": req["permission_level"],
                "status": req["status"],
                "reason": access_result["reason"]
            })

    return {
        "total_requests": len(requests_data),
        "status_count": status_count,
        "sla_breach_count": len(sla_breaches),
        "sla_breach_ids": sla_breaches,
        "policy_violation_count": len(policy_violations),
        "policy_violations": policy_violations
    }


# ---------------------------------------------------------------------------
# 4. 과다권한
# ---------------------------------------------------------------------------
def collect_overprivilege_status(today=None):
    with open(os.path.join(BASE_DIR, "access_logs.json"), encoding="utf-8") as f:
        access_data = json.load(f)

    with open(os.path.join(BASE_DIR, "dept_history.json"), encoding="utf-8") as f:
        dept_data = json.load(f)

    report = overprivilege.generate_overprivilege_report(
        permissions=access_data.get("permissions", {}),
        usage_logs=access_data.get("logs", []),
        assigned_departments=dept_data.get("assigned", {}),
        current_departments=dept_data.get("current", {}),
        today=today
    )
    return report


# ---------------------------------------------------------------------------
# 5. 회수 이력
# ---------------------------------------------------------------------------
def collect_revoke_status(overprivilege_report, today=None):
    logs = revoke.run_revocation(overprivilege_report.get("candidates", []), today=today)

    status_count = {}
    for log in logs:
        status_count[log["status"]] = status_count.get(log["status"], 0) + 1

    return {
        "total_revoke_actions": len(logs),
        "status_count": status_count,
        "logs": logs
    }


# ---------------------------------------------------------------------------
# 종합 주간 리포트
# ---------------------------------------------------------------------------
def generate_weekly_report(today=None):
    today = today or datetime.now()

    rbac_status = collect_rbac_status()
    request_status = collect_request_status()
    overprivilege_report = collect_overprivilege_status(today=today)
    revoke_status = collect_revoke_status(overprivilege_report, today=today)

    report = {
        "generated_at": today.strftime("%Y-%m-%d"),
        "rbac_status": rbac_status,
        "policy_violations": {
            "count": request_status["policy_violation_count"],
            "items": request_status["policy_violations"]
        },
        "request_status": {
            "total_requests": request_status["total_requests"],
            "status_count": request_status["status_count"],
            "sla_breach_count": request_status["sla_breach_count"],
            "sla_breach_ids": request_status["sla_breach_ids"]
        },
        "overprivilege": overprivilege_report,
        "revoke_history": revoke_status
    }

    return report


# ---------------------------------------------------------------------------
# Markdown 리포트 저장
# ---------------------------------------------------------------------------
def save_weekly_report_md(report, output_dir=None, today=None):
    today = today or datetime.now()
    output_dir = output_dir or BASE_DIR
    filename = f"access_control_weekly_report_{today.strftime('%Y%m%d')}.md"
    path = os.path.join(output_dir, filename)

    lines = []
    lines.append(f"# 접근통제 주간 리포트 ({report['generated_at']})")
    lines.append("")

    lines.append("## 1. RBAC 상태")
    rbac_status = report["rbac_status"]
    lines.append(f"- 등록된 역할 수: {rbac_status['total_roles']} ({', '.join(rbac_status['roles'])})")
    lines.append(f"- 역할이 부여된 사용자 수: {rbac_status['total_users']}")
    for user, role in rbac_status["user_roles"].items():
        lines.append(f"  - {user}: {role}")
    lines.append("")

    lines.append("## 2. 정책 위반")
    violations = report["policy_violations"]
    lines.append(f"- 위반 건수: {violations['count']}건")
    for item in violations["items"]:
        lines.append(
            f"  - [{item['request_id']}] {item['user']} / {item['system']} / "
            f"{item['permission_level']} (상태: {item['status']}) - {item['reason']}"
        )
    lines.append("")

    lines.append("## 3. 요청 처리 현황")
    req_status = report["request_status"]
    lines.append(f"- 전체 요청 수: {req_status['total_requests']}건")
    for status, count in req_status["status_count"].items():
        lines.append(f"  - {status}: {count}건")
    lines.append(f"- SLA 초과 건수: {req_status['sla_breach_count']}건 {req_status['sla_breach_ids']}")
    lines.append("")

    lines.append("## 4. 과다권한")
    overprivilege_report = report["overprivilege"]
    summary = overprivilege_report["summary"]
    lines.append(f"- 미사용 권한 사용자 수: {summary['unused_permission_users']}")
    lines.append(f"- 미사용 권한 건수: {summary['unused_permission_cases']}")
    lines.append(f"- 부서 불일치 건수: {summary['department_mismatch_cases']}")
    lines.append(f"- 과다권한 후보 총합: {summary['total_candidates']}")
    for candidate in overprivilege_report["candidates"]:
        lines.append(f"  - {candidate}")
    lines.append("")

    lines.append("## 5. 회수 이력")
    revoke_status = report["revoke_history"]
    lines.append(f"- 회수 처리 건수: {revoke_status['total_revoke_actions']}건")
    for status, count in revoke_status["status_count"].items():
        lines.append(f"  - {status}: {count}건")
    for log in revoke_status["logs"]:
        lines.append(
            f"  - {log['username']} / {log['permission']} / {log['action']} "
            f"(상태: {log['status']}, 사유: {log['reason']})"
        )
    lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return path


if __name__ == "__main__":
    report = generate_weekly_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))

    json_path = os.path.join(
        BASE_DIR, f"access_control_weekly_report_{datetime.now().strftime('%Y%m%d')}.json"
    )
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    md_path = save_weekly_report_md(report)
    print(f"\nJSON 저장 완료: {json_path}")
    print(f"Markdown 저장 완료: {md_path}")
