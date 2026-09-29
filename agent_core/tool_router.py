"""
에이전트 도구 라우터

access_control 모듈의 핵심 함수를 tool_registry 에 등록해,
LLM 에이전트가 도구 이름만으로 접근통제 기능을 호출할 수 있게 한다.
(agent/5day/tool_router.py 의 route_tool_call 패턴을 그대로 재사용)
"""

import os
import sys

ACCESS_CONTROL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "access_control")
sys.path.insert(0, os.path.abspath(ACCESS_CONTROL_DIR))

import rbac
import policy
import requests_flow
import overprivilege
import revoke
import weekly_report


def tool_evaluate_access(args):
    return policy.evaluate_access(args["username"], args["system"], args["requested_permission"])


def tool_assign_role(args):
    ok, message = rbac.assign_role(args["username"], args["role"])
    return {"ok": ok, "message": message}


def tool_revoke_role(args):
    ok, message = rbac.revoke_role(args["username"])
    return {"ok": ok, "message": message}


def tool_create_request(args):
    return requests_flow.create_request(
        args["user"], args["department"], args["system"],
        args["permission_level"], args["approver"]
    )


def tool_check_sla_breaches(args):
    return requests_flow.check_and_alert_sla_breaches()


def tool_generate_overprivilege_report(args):
    return overprivilege.generate_overprivilege_report(
        permissions=args["permissions"],
        usage_logs=args["usage_logs"],
        assigned_departments=args["assigned_departments"],
        current_departments=args["current_departments"]
    )


def tool_run_revocation(args):
    return revoke.run_revocation(args["candidates"])


def tool_generate_weekly_report(args):
    return weekly_report.generate_weekly_report()


tool_registry = {
    "evaluate_access": tool_evaluate_access,
    "assign_role": tool_assign_role,
    "revoke_role": tool_revoke_role,
    "create_request": tool_create_request,
    "check_sla_breaches": tool_check_sla_breaches,
    "generate_overprivilege_report": tool_generate_overprivilege_report,
    "run_revocation": tool_run_revocation,
    "generate_weekly_report": tool_generate_weekly_report,
}


def route_tool_call(tool_name, args=None):
    args = args or {}
    if tool_name in tool_registry:
        function_to_run = tool_registry[tool_name]
        return function_to_run(args)
    else:
        print(tool_name + "라는 도구는 없습니다.")
        return None


if __name__ == "__main__":
    print("--- 등록된 도구 목록 ---")
    print(list(tool_registry.keys()))

    print("\n--- evaluate_access 연동 확인 ---")
    result = route_tool_call("evaluate_access", {
        "username": "kim", "system": "개발 시스템", "requested_permission": "조회"
    })
    print(result)

    print("\n--- generate_weekly_report 연동 확인 ---")
    report = route_tool_call("generate_weekly_report")
    print("RBAC 사용자 수:", report["rbac_status"]["total_users"])
    print("정책 위반 건수:", report["policy_violations"]["count"])
    print("요청 총 건수:", report["request_status"]["total_requests"])
    print("과다권한 후보 수:", report["overprivilege"]["summary"]["total_candidates"])
    print("회수 처리 건수:", report["revoke_history"]["total_revoke_actions"])

    print("\n--- 존재하지 않는 도구 호출 ---")
    route_tool_call("no_such_tool")
