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
현재 시간은 {current_time} (대한민국 표준시, KST) 입니다.

아래 안내문에서 "캘린더에 넣을 대표 일정 1개"를 추출하여 JSON으로만 출력하십시오.

반드시 아래 규칙을 따르십시오.

[목표]
- 긴 안내문이어도 대표 일정 1개로 정리할 것
- 교육/행사/회의가 여러 세션으로 구성되어 있으면
  전체 일정을 하나의 대표 일정으로 요약할 것
- 세부 시간표는 details에 줄바꿈으로 정리할 것

[JSON 형식]
{{
  "title": "문자에서 가장 핵심이 되는 대표 일정명",
  "start_date": "YYYYMMDDTHHMMSS",
  "end_date": "YYYYMMDDTHHMMSS",
  "location": "장소 없으면 빈 문자열",
  "details": "준비물, 도착시간, 세부 일정표 포함. 없으면 빈 문자열"
}}

[대표 일정 추출 규칙]
1. 날짜 범위가 있으면 전체 기간을 대표 일정으로 잡을 것
2. '오전 9시 40분까지 도착' 같은 문구가 있으면 시작시간은 도착시간으로 설정
3. 마지막 세션 종료시간이 있으면 end_date는 그 종료시간으로 설정
4. 세부 과목/세션은 details에 모두 넣을 것
5. 날짜는 반드시 YYYYMMDDTHHMMSS 형식만 사용할 것
6. ISO 8601 형식 사용 금지
7. JSON 외 텍스트 절대 출력 금지

[예시 해석]
- 2026-04-13~2026-04-14 교육
- 오전 9:40까지 도착
- 2일차 마지막 종료 16:50
라면
start_date = 20260413T094000
end_date   = 20260414T165000

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

    if not validate_gcal_date(data.get("start_date", "")):
        raise ValueError(f"start_date 형식 오류: {data.get('start_date')}")
    if not validate_gcal_date(data.get("end_date", "")):
        raise ValueError(f"end_date 형식 오류: {data.get('end_date')}")

    return data

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
                data = process_text(user_input)

                st.subheader("추출된 데이터")
                st.json(data)

                title_encoded = urllib.parse.quote(data.get("title", "새 일정"), safe="")
                location_encoded = urllib.parse.quote(data.get("location", ""), safe="")
                details_encoded = urllib.parse.quote(data.get("details", ""), safe="")
                start_date = data["start_date"]
                end_date = data["end_date"]

                calendar_url = (
                    "https://calendar.google.com/calendar/render"
                    f"?action=TEMPLATE"
                    f"&text={title_encoded}"
                    f"&dates={start_date}/{end_date}"
                    f"&ctz=Asia%2FSeoul"
                    f"&location={location_encoded}"
                    f"&details={details_encoded}"
                )

                st.success("✅ 분석 완료! 아래 버튼을 눌러 캘린더에 최종 저장하세요.")

                html_button = f"""
                <a href="{calendar_url}" target="_blank">
                    <button style="
                        width:100%;
                        background-color:#4285F4;
                        color:white;
                        padding:15px;
                        border:none;
                        border-radius:8px;
                        font-size:16px;
                        font-weight:bold;
                        margin-bottom:10px;
                        cursor:pointer;">
                        🗓️ 캘린더 앱에 저장하기
                    </button>
                </a>
                """
                st.markdown(html_button, unsafe_allow_html=True)

                st.button("초기화 및 새 일정 입력", on_click=clear_text)

            except Exception as e:
                st.error("처리 중 오류가 발생했습니다. 텍스트를 다시 확인해 주세요.")
                st.write(e)
