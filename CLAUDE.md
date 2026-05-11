# CLAUDE.md — auto_addcalender 작업 가이드

## 프로젝트 개요

- **앱명**: AI 일정 자동 등록 (Omni-Sync Mobile)
- **스택**: Python 3.11, Streamlit, OpenAI GPT-4o
- **진입점**: `app.py` (428줄), 유틸리티: `date_utils.py`

## 브랜치 규칙

| 규칙 | 내용 |
|------|------|
| 메인 브랜치 | `main` |
| 작업 브랜치 형식 | `main_auto_addcalender_MMDD` |
| `main` 직접 커밋 | **금지** |
| `reset --hard` | **금지** |
| `clean -fd` | **금지** |

## 작업 순서

1. `main`에서 작업 브랜치 생성
2. 프로젝트 구조 점검 후 변경 범위 보고
3. 기존 기능 보존하며 수정
4. 커밋 후 PR 생성

## 금지 사항

- `main` 브랜치에 직접 push/commit
- 기존 일정 추출 로직(`process_text`, `build_calendar_url`, `build_ics_content`) 임의 변경
- OpenAI 프롬프트 무단 수정
- 전체 테스트 불필요 실행 (문서·설정 변경 시 테스트 생략 가능)

## 환경 변수

- `OPENAI_API_KEY`: Streamlit secrets 또는 `.env` (`.gitignore` 적용됨)

## 커밋 보고 형식

```
- commit hash:
- 수정 파일:
- 테스트 결과:
- PR 링크:
```

## Auto Dev Queue 파일

| 파일 | 역할 |
|------|------|
| `TASKS.md` | 작업 큐 및 상태 관리 |
| `AGENTS.md` | 에이전트별 역할 정의 |
| `.github/workflows/ci.yml` | CI 파이프라인 |
