# Day5 접근통제 결과 리포트 자동화 완성 및 발표 (슬라이드 요약)

원본 발표자료(디자인 포함): https://claude.ai/artifact/MCGH2xDiTcpk9jwqPGoUyX

## 1. 표지
접근통제 결과 리포트 자동화 완성 및 발표 — 1~4일차 모듈(RBAC·정책·요청·과다권한·회수)을
통합해 주간 리포트를 자동 생성하고, agent_core와 연동한다.

## 2. 목표
- 120분 진행: 핵심 코드 20~30분 직접 작성 → Codex·Claude Code로 확장·완성
- 평가 기준: 1~4일차 모듈 오류 없이 통합, 실무에 쓸 수 있는 주간 리포트, agent_core 연동 지점 설명
- 산출물: weekly_report.py · weekly_report_*.md · day05_retrospective.md

## 3. 5개 구조
| # | 영역 | 확인 내용 |
|---|---|---|
| 1 | RBAC 상태 | 사용자에게 부여된 역할과 권한 상태 |
| 2 | 정책 위반 | 정책에 맞지 않는 접근 발생 여부 |
| 3 | 요청 처리 현황 | 접근 요청·승인·반려·SLA 초과 현황 |
| 4 | 과다권한 | 미사용 권한, 부서 불일치 등 탐지 결과 |
| 5 | 회수 이력 | 실제 권한 회수 및 회수 사유 |

각 영역은 1~4일차에서 만든 기존 산출물을 그대로 재사용한다.

## 4. 데이터 흐름
1일차(roles.json, policy_matrix.json, exceptions.json) → RBAC 상태·정책 위반
2일차(requests.json) → 요청 처리 현황
3일차(overprivilege_report_YYYYMMDD.json) → 과다권한 결과
4일차(revoke_logs.json) → 회수 이력
→ 5일차: `weekly_report.py`가 5개 결과를 하나의 주간 리포트로 통합

## 5. 통합하면서 바뀐 점
1. **서로 다른 데이터 모양을 하나로 흡수** — 과다권한 후보가 "미사용 권한"이냐
   "부서 불일치"냐에 따라 가진 키가 다름 →
   `candidate.get("permission", candidate.get("system", "부서권한"))` 로 한 곳에서 흡수
2. **저장된 상태값을 믿지 않고 다시 검증** — `requests.json`의 status를 그대로 읽는 대신
   요청 전체를 `policy.evaluate_access()`로 재판정 → 이미 승인된 요청도 위반으로 재탐지 가능
3. **서로 다른 폴더에 있던 모듈을 경로로 연결** — `access_control`과 `agent_core`는 형제
   폴더라 import가 안 되어, `tool_router.py`에서 `sys.path.insert()`로 연결
4. **순환 참조 구조는 그대로 유지** — `rbac.py` ↔ `policy.py`가 서로를 함수 안에서만
   import하던 기존 패턴을 살려 `weekly_report.py`가 두 모듈을 동시에 import해도 충돌 없음

## 6. weekly_report.py 구현
```python
def generate_weekly_report():
    rbac_status = collect_rbac_status()
    request_status = collect_request_status()
    overprivilege = collect_overprivilege_status()
    revoke_status = collect_revoke_status(overprivilege)
    return {...}
```
- 5개 모듈(rbac·policy·requests_flow·overprivilege·revoke)을 그대로 import해서 재사용
- 정책 위반은 requests.json의 모든 요청을 `policy.evaluate_access()`로 재검증해 판정
- `save_weekly_report_md()`가 `access_control_weekly_report_YYYYMMDD.md` 자동 저장

## 7. agent_core/tool_router.py 연동
등록된 도구: `evaluate_access`, `assign_role`/`revoke_role`, `create_request`,
`check_sla_breaches`, `generate_overprivilege_report`, `run_revocation`,
`generate_weekly_report`

`route_tool_call("generate_weekly_report")` → 연동 테스트 결과 정상 호출 확인

## 8. 통합하고 나서야 보인 것들 (코드 리뷰)
- **이미 "승인"된 요청도 재검증하니 위반으로 잡힘**: REQ-005(jung / 운영 시스템 / 수정)는
  requests.json에 상태: 승인으로 저장돼 있었지만, `policy.evaluate_access()`로 재판정하자
  "등록되지 않은 사용자" 위반으로 탐지됨 — 상태값만 믿었다면 놓쳤을 사례
- **같은 이름의 데이터가 두 곳에 존재**: `access_control/requests.json`(실제 운영 데이터)과
  `config/requests.json`(샘플 데이터)이 이름이 같아 혼동 위험 → 경로를 명확히 확인하고 재사용
- **실습용 스크립트(day4_4.py) 문법 오류는 정식 모듈로 대체**: 딕셔너리 리터럴 오류가 있던
  연습 코드는 손보지 않고, 같은 로직을 `revoke.py`로 새로 정리해 통합 대상에서 제외

## 9. 실행 결과 (2026-09-29 기준)
- RBAC 사용자 4명 (역할 4종 보유)
- 정책 위반 3건 (REQ-003~005)
- 요청 처리 5건 (승인 3 · 반려 2, SLA 초과 0건)
- 과다권한 후보 6건 (미사용 4 · 불일치 2)
- 회수 처리 6건 (알림 4 · 승인대기 2)
- `access_control_weekly_report_20260929.md` / `.json` 자동 저장 완료
- GitHub 공개 저장소로 공유 → 다른 PC에서 clone 후 동일하게 정상 실행 확인

## 10. 다음 단계
- 회수 이력 누적: `revoke_logs`를 매번 덮어쓰지 않고 append하여 시계열로 추적
- 정책 위반 범위 확장: `requests.json` 외 실시간 접근 로그까지 판정에 포함
- 실습 파일 정리: `day4_4.py` 등 연습용 스크립트를 `drafts/`로 분리

agent_core ↔ access_control 연동 완료, GitHub 공개 배포까지 확인
→ github.com/alska14/access-control-weekly-report
