# 접근통제 결과 리포트 자동화 (Day 5)

RBAC · 정책 위반 · 접근 요청 처리 · 과다권한 · 권한 회수, 5개 영역의 결과를
하나의 주간 리포트로 자동 생성하고 LLM 에이전트(`agent_core`)에서 바로 호출할 수 있게
연동한 프로젝트입니다.

발표자료: [Day5 접근통제 결과 리포트 자동화 완성 및 발표](https://claude.ai/artifact/MCGH2xDiTcpk9jwqPGoUyX)
(슬라이드 텍스트 요약은 [docs/PRESENTATION.md](docs/PRESENTATION.md) 참고)

## 폴더 구조

```
access_control/
  rbac.py              # 사용자 ↔ 역할(부서) 관리
  policy.py            # 정책 매트릭스 기반 권한 판단 + 예외 승인 검사
  requests_flow.py     # 접근 요청 생성/승인/반려, SLA 초과 감지
  overprivilege.py     # 미사용 권한 · 부서 불일치 탐지
  revoke.py            # 과다권한 후보에 대한 회수 처리 및 이력 생성
  weekly_report.py     # 위 5개 모듈을 통합한 주간 리포트 생성기
  *.json               # 각 모듈이 사용하는 샘플/결과 데이터
  day05_retrospective.md
agent_core/
  tool_router.py       # access_control 핵심 함수를 도구로 등록해 에이전트가 호출
config/
  roles.json, user_roles.json, policy.json, requests.json, sla_config.json
```

## 실행 방법

```bash
# 5개 영역을 통합한 주간 리포트 생성 (.md / .json 자동 저장)
cd access_control
python weekly_report.py

# 에이전트 도구 라우터로 access_control 기능 호출 연동 확인
cd ../agent_core
python tool_router.py
```

## 무엇을 통합했나

`weekly_report.py`의 `generate_weekly_report()`가 아래 5개 모듈을 그대로 불러와
하나의 딕셔너리로 합칩니다.

| 영역 | 재사용 모듈 | 확인 내용 |
|---|---|---|
| RBAC 상태 | `rbac.py` | 사용자에게 부여된 역할과 권한 상태 |
| 정책 위반 | `policy.py` | 저장된 요청 상태를 다시 `evaluate_access()`로 재검증한 위반 여부 |
| 요청 처리 현황 | `requests_flow.py` | 접근 요청 승인·반려·SLA 초과 현황 |
| 과다권한 | `overprivilege.py` | 미사용 권한, 부서 불일치 탐지 결과 |
| 회수 이력 | `revoke.py` | 과다권한 후보에 대한 실제 회수 처리 및 사유 |

`agent_core/tool_router.py`는 `access_control`과 서로 다른 최상위 폴더이기 때문에
`sys.path.insert()`로 경로를 연결한 뒤, 위 5개 모듈의 핵심 함수를 `tool_registry`에
등록해 `route_tool_call("generate_weekly_report")`처럼 도구 이름만으로 호출할 수
있게 했습니다.

## 통합 과정에서 발견한 것

- **저장된 상태값만 믿으면 놓치는 위반**: `requests.json`에 `REQ-005`(사용자 `jung`)가
  이미 "승인" 상태로 저장돼 있었지만, `weekly_report.py`가 `policy.evaluate_access()`로
  전체 요청을 다시 판정하자 "등록되지 않은 사용자" 위반으로 탐지되었습니다. 저장된
  status만 집계했다면 놓쳤을 사례입니다.
- **과다권한 후보의 데이터 모양이 서로 다름**: "미사용 권한" 후보는 `permission` 키를
  갖지만 "부서 불일치" 후보는 갖지 않아, `revoke.py`에서
  `candidate.get("permission", candidate.get("system", "부서권한"))` 형태로
  두 모양을 한 곳에서 흡수하도록 처리했습니다.
- **같은 이름의 데이터가 두 곳에 존재**: `access_control/requests.json`(실제 운영
  데이터)과 `config/requests.json`(샘플 데이터)이 이름이 같아 혼동될 수 있어,
  `requests_flow.py`가 바라보는 경로를 명확히 확인하고 그대로 재사용했습니다.

## 검증

- 각 모듈을 직접 실행해 정상 동작 및 예외 케이스(미등록 사용자·부서 없음 등)를 확인했습니다.
- GitHub 공개 저장소로 공유 후, 다른 PC에서 `git clone` 하여 동일하게 정상 실행되는 것을
  확인했습니다.
