# 접근통제 주간 리포트 (2026-09-29)

## 1. RBAC 상태
- 등록된 역할 수: 4 (개발팀, 인사팀, 보안팀, 운영팀)
- 역할이 부여된 사용자 수: 4
  - kim: 개발팀
  - lee: 인사팀
  - park: 보안팀
  - choi: 운영팀

## 2. 정책 위반
- 위반 건수: 3건
  - [REQ-003] lee / 보안 시스템 / 관리자 (상태: 반려) - 정책 위반이며 유효한 예외 승인도 없습니다.
  - [REQ-004] choi / 테스트 시스템 / 조회 (상태: 반려) - 정책 위반이며 유효한 예외 승인도 없습니다.
  - [REQ-005] jung / 운영 시스템 / 수정 (상태: 승인) - 등록되지 않은 사용자입니다.

## 3. 요청 처리 현황
- 전체 요청 수: 5건
  - 승인: 3건
  - 반려: 2건
- SLA 초과 건수: 0건 []

## 4. 과다권한
- 미사용 권한 사용자 수: 4
- 미사용 권한 건수: 4
- 부서 불일치 건수: 2
- 과다권한 후보 총합: 6
  - {'username': 'kim', 'type': '미사용 권한', 'permission': 'manage_security', 'last_used': '2026-05-01', 'reason': '90일 이상 미사용'}
  - {'username': 'lee', 'type': '미사용 권한', 'permission': 'admin', 'last_used': '2026-04-01', 'reason': '90일 이상 미사용'}
  - {'username': 'park', 'type': '미사용 권한', 'permission': 'read_log', 'last_used': '2026-01-01', 'reason': '90일 이상 미사용'}
  - {'username': 'choi', 'type': '미사용 권한', 'permission': 'export_data', 'last_used': None, 'reason': '90일 이상 미사용'}
  - {'username': 'kim', 'type': '부서 불일치', 'assigned_department': '개발팀', 'current_department': '보안팀', 'reason': '권한 부여 당시 부서와 현재 부서가 다름'}
  - {'username': 'choi', 'type': '부서 불일치', 'assigned_department': '마케팅팀', 'current_department': None, 'reason': '권한 부여 당시 부서와 현재 부서가 다름'}

## 5. 회수 이력
- 회수 처리 건수: 6건
  - 회수 예정 알림: 4건
  - 승인 대기: 2건
  - kim / manage_security / 즉시 알림 후 유예 회수 (상태: 회수 예정 알림, 사유: 90일 이상 미사용)
  - lee / admin / 즉시 알림 후 유예 회수 (상태: 회수 예정 알림, 사유: 90일 이상 미사용)
  - park / read_log / 즉시 알림 후 유예 회수 (상태: 회수 예정 알림, 사유: 90일 이상 미사용)
  - choi / export_data / 즉시 알림 후 유예 회수 (상태: 회수 예정 알림, 사유: 90일 이상 미사용)
  - kim / 부서권한 / 승인 필요 (상태: 승인 대기, 사유: 권한 부여 당시 부서와 현재 부서가 다름)
  - choi / 부서권한 / 승인 필요 (상태: 승인 대기, 사유: 권한 부여 당시 부서와 현재 부서가 다름)
