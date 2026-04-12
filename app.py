import streamlit as st
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
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return date_str

def clear_text():
    st.session_state.input_text = ""

user_input = st.text_area(
    "일정 내용을 입력하세요",
    key="input_text",
    placeholder="복사한 텍스트를 붙여넣으세요."
)

if st.button("일정 파싱 및 캘린더 열기"):
    if user_input.strip():
        with st.spinner("AI 분석 중..."):
            try:
                events = process_text(user_input)

                st.subheader(f"추출된 일정 ({len(events)}개)")

                for i, event in enumerate(events):
                    st.markdown(f"---")
                    st.markdown(f"**일정 {i+1}**")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**제목:** {event.get('title', '')}")
                        st.markdown(f"**시작:** {format_display_date(event['start_date'])}")
                        st.markdown(f"**종료:** {format_display_date(event['end_date'])}")
                    with col2:
                        if event.get("location"):
                            st.markdown(f"**장소:** {event['location']}")
                        if event.get("details"):
                            st.markdown(f"**메모:**")
                            st.text(event["details"])

                    url = build_calendar_url(event)
                    html_button = f"""
                    <a href="{url}" target="_blank">
                        <button style="
                            width:100%;
                            background-color:#4285F4;
                            color:white;
                            padding:14px;
                            border:none;
                            border-radius:8px;
                            font-size:15px;
                            font-weight:bold;
                            margin-bottom:6px;
                            cursor:pointer;">
                            🗓️ 일정 {i+1} 캘린더에 저장
                        </button>
                    </a>
                    """
                    st.markdown(html_button, unsafe_allow_html=True)

                st.markdown("---")
                st.success(f"✅ {len(events)}개 일정 분석 완료!")
                st.button("초기화 및 새 일정 입력", on_click=clear_text)

            except Exception as e:
                st.error("처리 중 오류가 발생했습니다. 텍스트를 다시 확인해 주세요.")
                st.write(e)
