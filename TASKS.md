# TASKS.md — Auto Dev Queue

## 상태 범례

| 심볼 | 상태 |
|------|------|
| `[ ]` | 대기 |
| `[~]` | 진행 중 |
| `[x]` | 완료 |
| `[!]` | 블로킹 |

---

## 완료된 작업

- [x] GitHub 저장소 clone 및 로컬-원격 동기화 확인 (2026-05-10)
- [x] 작업 브랜치 `main_auto_addcalender_0510` 생성 (2026-05-11)
- [x] 프로젝트 구조 점검 및 Auto Dev Queue 적용 가능 여부 확인 (2026-05-11)
- [x] README.md 생성 (2026-05-11)
- [x] CLAUDE.md 생성 (2026-05-11)
- [x] TASKS.md 생성 (2026-05-11)
- [x] AGENTS.md 생성 (2026-05-11)
- [x] GitHub Actions CI workflow 생성 (2026-05-11)

---

## 대기 중인 작업

- [ ] Streamlit Cloud 배포 설정 확인 및 문서화
- [ ] `date_utils.py` 엣지케이스 단위 테스트 추가 (`tests/test_date_utils.py`)
- [ ] OpenAI 프롬프트 버전 관리 분리 (별도 파일 또는 상수)
- [ ] `.env.example` 파일 추가 (로컬 개발 환경 설정 가이드)
- [ ] 카카오 캘린더 `.ics` 인코딩 이슈 검증 (한글 파일명)

---

## 작업 추가 방법

새 작업은 아래 형식으로 "대기 중인 작업" 섹션에 추가:

```
- [ ] 작업 내용 (담당: AGENT명, 기한: YYYY-MM-DD)
```
