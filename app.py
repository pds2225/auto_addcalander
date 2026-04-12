import streamlit as st
from datetime import datetime
from openai import OpenAI
import json

# UI 설정
st.set_page_config(page_title="Omni-Sync Mobile", layout="centered")
st.title("📅 AI 일정 자동 등록 (Mobile)")

# 환경 변수에서 API 키 로드 (Streamlit Cloud 설정에서 입력)
api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)

# 텍스트 분석 함수
def process_text(text):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prompt = f"현재 시간 {current_time}. 다음 텍스트에서 일정 정보를 추출해 JSON으로 출력해: {text}"
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={ "type": "json_object" }
    )
    return json.loads(response.choices[0].message.content)

# 입력창
user_input = st.text_area("일정 내용을 입력하세요", placeholder="예: 내일 오후 2시 강남역 미팅")

if st.button("즉시 등록"):
    if user_input:
        with st.spinner('분석 중...'):
            data = process_text(user_input)
            st.json(data)
            st.success("일정이 분석되었습니다. (API 연동 시 자동 등록)")
