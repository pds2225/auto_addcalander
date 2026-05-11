# AGENTS.md — 에이전트 역할 정의

## Auto Dev Queue 에이전트 구성

---

### AGENT-01: sync-checker

**역할**: Git 동기화 점검  
**트리거**: 작업 시작 전, PR 생성 전  
**수행 작업**:
- `git fetch --prune origin`
- `HEAD` vs `origin/main` 비교
- `git status --short` 확인
- 결과를 12줄 이내 보고

**금지**: commit, push, pull, reset, clean

---

### AGENT-02: branch-manager

**역할**: 작업 브랜치 생성 및 관리  
**트리거**: 새 작업 시작  
**수행 작업**:
- `main_프로젝트명_MMDD` 형식 브랜치 생성
- 브랜치 존재 여부 확인 후 중복 방지
- 작업 완료 후 PR 생성 보조

**브랜치 규칙**: `main_auto_addcalender_MMDD`

---

### AGENT-03: structure-auditor

**역할**: 프로젝트 구조 점검 및 Auto Dev Queue 적용 가능 여부 평가  
**트리거**: 신규 저장소 연결 시, 주요 작업 시작 전  
**수행 작업**:
- 파일 목록 및 변경 범위 보고
- README, TASKS, AGENTS, workflow, scripts 존재 여부 확인
- 파일 본문 분석은 필요 최소한으로 제한

---

### AGENT-04: doc-writer

**역할**: 문서 파일 생성 및 유지  
**트리거**: 문서 파일 부재 감지 시  
**수행 작업**:
- `README.md`, `CLAUDE.md`, `TASKS.md`, `AGENTS.md` 생성/갱신
- 기존 코드 기능에 영향 없는 순수 문서 작업
- 테스트 생략 가능

---

### AGENT-05: ci-configurator

**역할**: GitHub Actions CI/CD 파이프라인 설정  
**트리거**: `.github/workflows/` 부재 시  
**수행 작업**:
- `ci.yml` 생성 (lint, 의존성 설치 검증)
- Streamlit 앱 구동 가능 여부 기본 확인
- secrets 설정 가이드 제공

---

## 에이전트 실행 순서 (표준 워크플로)

```
sync-checker → branch-manager → structure-auditor → doc-writer → ci-configurator
```

## 보고 형식 (모든 에이전트 공통)

```
- commit hash:
- 수정 파일:
- 테스트 결과:
- PR 링크:
```
