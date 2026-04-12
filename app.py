import streamlit as st
from datetime import datetime, timedelta
from openai import OpenAI
import json
import urllib.parse

st.set_page_config(page_title="Omni-Sync Mobile", layout="centered")
st.title("📅 AI 일정 자동 등록")

api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)

# 상태 관리: 입력창 초기화를 위한 변수 설정
if "input_text" not in st.session_state:
    st.session_state.input_text = ""

def process_text(text):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # [수정 1] 시간 추출 및 정형화(ISO 8601 유사)를 위한 프롬프트 강화
    prompt = f"""
    현재 시간은 {current_time} 입니다. 이 기준을 바탕으로 다음 텍스트에서 일정 정보를 추출하여 JSON으로 출력하십시오.
    
    [JSON Key 필수 규격]
    - title: 일정 제목
    - start_date: 시작 시간 (반드시 YYYYMMDDTHHMMSS 포맷, 예: 20260412T150000)
    - end_date: 종료 시간 (반드시 YYYYMMDDTHHMMSS 포맷. 단, 텍스트에 종료 시간이 없다면 start_date에서 1시간을 더한 시간으로 자동 계산할 것)
    - location: 장소 (없으면 빈 문자열)
    - details: 준비물 등 기타 참고사항 (없으면 빈 문자열)
    
    텍스트: {text}
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={ "type": "json_object" },
        temperature=0.1 # 환각(Hallucination) 최소화를 위해 창의성 낮춤
    )
    return json.loads(response.choices[0].message.content)

# 콜백 함수: 처리 완료 후 텍스트 에어리어 초기화
def clear_text():
    st.session_state.input_text = ""

user_input = st.text_area("일정 내용을 입력하세요", key="input_text", placeholder="복사한 텍스트를 붙여넣으세요.")

if st.button("일정 파싱 및 캘린더 열기"):
    if user_input:
        with st.spinner('AI 분석 중...'):
            try:
                data = process_text(user_input)
                
                # 분석 결과 시각화
                st.subheader("추출된 데이터")
                st.json(data)
                
                # [수정 2] URL 파라미터 인코딩 및 시간 결합
                title_encoded = urllib.parse.quote(data.get("title", "새 일정"))
                location_encoded = urllib.parse.quote(data.get("location", ""))
                details_encoded = urllib.parse.quote(data.get("details", ""))
                
                start_date = data.get("start_date", "")
                end_date = data.get("end_date", "")
                
                # 구글 캘린더 생성 URL 템플릿 (dates 파라미터 추가)
                calendar_url = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={title_encoded}&dates={start_date}/{end_date}&location={location_encoded}&details={details_encoded}"
                
                st.success("✅ 분석 완료! 아래 버튼을 눌러 캘린더에 최종 저장하세요.")
                
                # 모바일 최적화 대형 버튼
                html_button = f"""
                <a href="{calendar_url}" target="_blank">
                    <button style="width:100%; background-color:#4285F4; color:white; padding:15px; border:none; border-radius:8px; font-size:16px; font-weight:bold; margin-bottom: 10px;">
                        🗓️ 캘린더 앱에 저장하기
                    </button>
                </a>
                """
                st.markdown(html_button, unsafe_allow_html=True)
                
                # [수정 3] 입력창 비우기 버튼 추가 (초기화 편의성)
                st.button("초기화 및 새 일정 입력", on_click=clear_text)
                
            except Exception as e:
                st.error("처리 중 오류가 발생했습니다. 텍스트를 다시 확인해 주세요.")
                st.write(e)
