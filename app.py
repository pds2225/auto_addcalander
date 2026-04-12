import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
from openai import OpenAI
import json
import urllib.parse
import re

st.set_page_config(page_title="Omni-Sync Mobile", layout="centered")
st.title("📅 AI 일정 자동 등록")

api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)

if "input_text" not in st.session_state:
    st.session_state.input_text = ""
if "events" not in st.session_state:
    st.session_state.events = []
if "auto_open_done" not in st.session_state:
    st.session_state.auto_open_done = False

def validate_gcal_date(date_str):
    return bool(re.match(r"^\d{8}T\d{6}$", str(date_str)))

def process_text(text):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    prompt = f"""
현재 시간은 {current_time} (KST) 입니다.

아래 안내문에서 날짜별로 일정을 분리하여 JSON 배열로만 출력하십시오.

[출력 형식]
{{
  "events": [
    {{
      "title": "핵심 일정명만",
      "start_date": "YYYYMMDDTHHMMSS",
      "end_date": "YYYYMMDDTHHMMSS",
      "location": "장소",
      "details": "해당 날짜의 세부 일정"
    }}
  ]
}}

[제목 규칙]
- 연도(2026년 등), 차수(제7차, 제3회 등), 기수(1기, 2기 등) 제거
- 핵심 행사명만 남길 것
- 예: "2026년 제7차 희망리턴패키지 재도전교육" → "희망리턴패키지 재도전교육"
- 모든 날짜 이벤트의 title은 동일하게 설정

[날짜 분리 규칙]
- 다일 행사는 날짜별로 각각 1개씩 이벤트 생성
- 각 이벤트의 start_date: 해당 날짜의 도착시간 또는 첫 세션 시작시간
- 각 이벤트의 end_date: 해당 날짜의 마지막 세션 종료시간 또는 퇴실시간
- 도착/퇴실 시간이 명시된 경우 그 시간을 사용
- 시간이 전혀 없는 경우 start=09:00, end=18:00으로 설정

[details 규칙]
- 해당 날짜에 해당하는 세션/과목만 포함
- "1일차" 또는 "2일차" 등 날짜 표시 첫 줄에 포함
- 준비물, 유의사항 등 공통 정보는 모든 날짜 이벤트에 포함
- 세부 시간표가 있으면 시간 순서대로 정리
- 장소 주차/교통 안내가 있으면 포함

[날짜 형식]
- 반드시 YYYYMMDDTHHMMSS 형식만 사용
- ISO 8601 금지
- JSON 외 텍스트 절대 출력 금지

텍스트:
{text}
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.1
    )

    data = json.loads(response.choices[0].message.content)
    events = data.get("events", [])

    if not events:
        raise ValueError("일정을 추출하지 못했습니다. 텍스트를 다시 확인해 주세요.")

    for i, event in enumerate(events):
        if not validate_gcal_date(event.get("start_date", "")):
            raise ValueError(f"이벤트 {i+1} start_date 형식 오류: {event.get('start_date')}")
        if not validate_gcal_date(event.get("end_date", "")):
            raise ValueError(f"이벤트 {i+1} end_date 형식 오류: {event.get('end_date')}")

    return events

def build_calendar_url(event):
    title_encoded = urllib.parse.quote(event.get("title", "새 일정"), safe="")
    location_encoded = urllib.parse.quote(event.get("location", ""), safe="")
    details_encoded = urllib.parse.quote(event.get("details", ""), safe="")
    start_date = event["start_date"]
    end_date = event["end_date"]

    return (
        "https://calendar.google.com/calendar/render"
        f"?action=TEMPLATE"
        f"&text={title_encoded}"
        f"&dates={start_date}/{end_date}"
        f"&ctz=Asia%2FSeoul"
        f"&location={location_encoded}"
        f"&details={details_encoded}"
    )

def format_display_date(date_str):
    try:
        dt = datetime.strptime(date_str, "%Y%m%dT%H%M%S")
        return dt.strftime("%m/%d(%a) %H:%M")
    except Exception:
        return date_str

def clear_all():
    st.session_state.input_text = ""
    st.session_state.events = []
    st.session_state.auto_open_done = False

# ── 입력 영역 ──────────────────────────────────────────
user_input = st.text_area(
    "일정 내용을 입력하세요",
    key="input_text",
    placeholder="복사한 텍스트를 붙여넣으세요."
)

if st.button("일정 등록", type="primary", use_container_width=True):
    if user_input.strip():
        with st.spinner("AI 분석 중..."):
            try:
                events = process_text(user_input)
                st.session_state.events = events
                st.session_state.auto_open_done = False
            except Exception as e:
                st.error("처리 중 오류가 발생했습니다. 텍스트를 다시 확인해 주세요.")
                st.write(e)
    else:
        st.warning("텍스트를 입력해 주세요.")

# ── 결과 영역 ──────────────────────────────────────────
if st.session_state.events:
    events = st.session_state.events

    # 최초 1회만 자동으로 구글 캘린더 탭 오픈
    if not st.session_state.auto_open_done:
        urls = [build_calendar_url(e) for e in events]
        js_opens = "\n".join([f'window.open("{url}", "_blank");' for url in urls])
        components.html(f"<script>{js_opens}</script>", height=1)
        st.session_state.auto_open_done = True

    st.success(f"✅ {len(events)}개 일정을 캘린더에 등록했습니다.")

    # 팝업 차단 대비 수동 버튼
    for i, event in enumerate(events):
        url = build_calendar_url(event)
        label = f"{format_display_date(event['start_date'])} ~ {format_display_date(event['end_date'])}"
        fallback = f"""
        <a href="{url}" target="_blank">
            <button style="
                width:100%;
                background-color:#34A853;
                color:white;
                padding:10px;
                border:none;
                border-radius:8px;
                font-size:14px;
                font-weight:bold;
                margin-bottom:6px;
                cursor:pointer;">
                🗓️ 일정 {i+1} 직접 열기 &nbsp;|&nbsp; {label}
            </button>
        </a>
        """
        st.markdown(fallback, unsafe_allow_html=True)

    st.caption("팝업이 차단된 경우 위 버튼을 직접 눌러주세요.")

    # ── 공유 기능 ──────────────────────────────────────
    st.markdown("---")
    st.subheader("📤 일정 공유")
    st.caption("공유할 일정을 선택하면 카카오톡 등으로 보낼 수 있는 링크를 생성합니다.")

    share_selections = []
    for i, event in enumerate(events):
        label = f"일정 {i+1}  |  {format_display_date(event['start_date'])}  {event.get('title', '')}"
        checked = st.checkbox(label, value=False, key=f"share_{i}")
        share_selections.append(checked)

    if st.button("공유 링크 생성", use_container_width=True):
        selected = [e for e, s in zip(events, share_selections) if s]
        if selected:
            lines = ["📅 일정을 공유합니다\n"]
            for event in selected:
                lines.append(f"▶ {event.get('title', '')}")
                lines.append(f"  {format_display_date(event['start_date'])} ~ {format_display_date(event['end_date'])}")
                if event.get("location"):
                    lines.append(f"  📍 {event['location']}")
                if event.get("details"):
                    for line in event["details"].splitlines():
                        lines.append(f"  {line}")
                lines.append(f"  🔗 구글캘린더 바로추가: {build_calendar_url(event)}")
                lines.append("")
            share_text = "\n".join(lines)
            st.text_area(
                "아래 내용을 복사해서 공유하세요",
                value=share_text,
                height=300
            )
        else:
            st.warning("공유할 일정을 1개 이상 선택해 주세요.")

    st.markdown("---")
    st.button("초기화 및 새 일정 입력", on_click=clear_all, use_container_width=True)
