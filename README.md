# AI 일정 자동 등록 (auto_addcalender)

텍스트를 붙여넣으면 GPT-4o가 일정을 추출해 구글 캘린더 또는 카카오 캘린더(.ics)에 바로 등록할 수 있는 Streamlit 웹 앱입니다.

## 기능

- 자연어 텍스트에서 일정(제목·날짜·장소·메모) 자동 추출
- 구글 캘린더 원클릭 등록 링크 생성
- 카카오 캘린더용 `.ics` 파일 다운로드
- 카카오톡 공유 / 클립보드 복사
- 날짜 범위 표기 자동 정규화 (`05-01~03` → `05-01~05-03`)

## 설치 및 실행

```bash
pip install -r requirements.txt
streamlit run app.py
```

앱은 기본적으로 `http://localhost:8501` 에서 실행됩니다.

## 환경 변수

| 키 | 설명 |
|----|------|
| `OPENAI_API_KEY` | OpenAI API 키 (Streamlit secrets 또는 `.env`) |

Streamlit Cloud 배포 시 `.streamlit/secrets.toml` 에 설정합니다:

```toml
OPENAI_API_KEY = "sk-..."
```

## 파일 구조

```
auto_addcalender/
├── app.py            # 메인 Streamlit 앱
├── date_utils.py     # 날짜 범위 정규화 유틸리티
├── requirements.txt  # 의존성 목록
├── .devcontainer/    # GitHub Codespaces 설정
└── .gitignore
```

## 브랜치 규칙

- 메인 브랜치: `main`
- 작업 브랜치: `main_auto_addcalender_MMDD` 형식
- `main` 직접 커밋 금지

## 기술 스택

- Python 3.11+
- [Streamlit](https://streamlit.io/)
- [OpenAI GPT-4o](https://platform.openai.com/)
- Google Calendar API (URL 방식, 인증 불필요)
