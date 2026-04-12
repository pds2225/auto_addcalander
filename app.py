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

# ── 세션 초기화 ────────────────────────────────────────
for key, default in {
    "input_text": "",
    "events": [],
    "parsed": False,
    "registered": False,
    "auto_open_done": False,
    "share_sels": [],
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ── 유틸 함수 ──────────────────────────────────────────
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
        temperature=0.1,
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
    return (
        "https://calendar.google.com/calendar/render"
        "?action=TEMPLATE"
        f"&text={urllib.parse.quote(event.get('title', '새 일정'), safe='')}"
        f"&dates={event['start_date']}/{event['end_date']}"
        "&ctz=Asia%2FSeoul"
        f"&location={urllib.parse.quote(event.get('location', ''), safe='')}"
        f"&details={urllib.parse.quote(event.get('details', ''), safe='')}"
    )


def fmt(date_str):
    try:
        return datetime.strptime(date_str, "%Y%m%dT%H%M%S").strftime("%m/%d(%a) %H:%M")
    except Exception:
        return date_str


def on_register():
    """등록 버튼 콜백 – 체크박스 값을 먼저 캡처한 후 상태 전환"""
    st.session_state.share_sels = [
        st.session_state.get(f"share_{i}", False)
        for i in range(len(st.session_state.events))
    ]
    st.session_state.registered = True
    st.session_state.auto_open_done = False


def clear_all():
    st.session_state.input_text = ""
    st.session_state.events = []
    st.session_state.parsed = False
    st.session_state.registered = False
    st.session_state.auto_open_done = False
    st.session_state.share_sels = []


# ══════════════════════════════════════════════════════
# 1단계: 입력 + 분석
# ══════════════════════════════════════════════════════
user_input = st.text_area(
    "일정 내용을 입력하세요",
    key="input_text",
    placeholder="복사한 텍스트를 붙여넣으세요.",
)

if st.button("일정 분석", use_container_width=True):
    if user_input.strip():
        with st.spinner("AI 분석 중..."):
            try:
                events = process_text(user_input)
                st.session_state.events = events
                st.session_state.parsed = True
                st.session_state.registered = False
                st.session_state.auto_open_done = False
                st.session_state.share_sels = []
            except Exception as e:
                st.error("처리 중 오류가 발생했습니다. 텍스트를 다시 확인해 주세요.")
                st.write(e)
    else:
        st.warning("텍스트를 입력해 주세요.")


# ══════════════════════════════════════════════════════
# 2단계: 미리보기 + 공유 체크 + 등록 버튼
# ══════════════════════════════════════════════════════
if st.session_state.parsed and not st.session_state.registered and st.session_state.events:
    events = st.session_state.events

    st.markdown("---")
    st.subheader(f"등록 내용 확인  ·  총 {len(events)}개 일정")
    st.caption("내용을 확인한 후 아래 [등록하기] 버튼을 누르세요. 공유할 일정은 체크하세요.")

    for i, event in enumerate(events):
        with st.container(border=True):
            # 제목 행
            col_title, col_share = st.columns([5, 1])
            with col_title:
                st.markdown(f"**일정 {i+1} &nbsp; {event.get('title', '')}**")
            with col_share:
                st.checkbox("공유", key=f"share_{i}", value=False, label_visibility="visible")

            # 날짜/장소 행
            st.markdown(
                f"📅 &nbsp; {fmt(event['start_date'])} &nbsp;~&nbsp; {fmt(event['end_date'])}"
            )
            if event.get("location"):
                st.markdown(f"📍 &nbsp; {event['location']}")

            # 메모 (접어두기)
            if event.get("details"):
                with st.expander("📝 메모 보기"):
                    st.text(event["details"])

    st.markdown("")
    st.button(
        "✅ 캘린더에 등록하기",
        on_click=on_register,
        type="primary",
        use_container_width=True,
    )


# ══════════════════════════════════════════════════════
# 3단계: 자동 등록 실행 + 공유 텍스트
# ══════════════════════════════════════════════════════
if st.session_state.registered and st.session_state.events:
    events = st.session_state.events
    share_sels = st.session_state.share_sels

    # 최초 1회 자동으로 구글 캘린더 탭 오픈
    if not st.session_state.auto_open_done:
        urls = [build_calendar_url(e) for e in events]
        js_opens = "\n".join([f'window.open("{u}", "_blank");' for u in urls])
        components.html(f"<script>{js_opens}</script>", height=1)
        st.session_state.auto_open_done = True

    st.markdown("---")
    st.success(f"✅ {len(events)}개 일정을 캘린더에 등록했습니다!")

    # 팝업 차단 대비 수동 버튼
    st.caption("팝업이 차단된 경우 아래 버튼으로 직접 여세요.")
    for i, event in enumerate(events):
        url = build_calendar_url(event)
        st.markdown(
            f'<a href="{url}" target="_blank">'
            f'<button style="width:100%;background:#34A853;color:white;padding:10px;'
            f'border:none;border-radius:8px;font-size:14px;font-weight:bold;'
            f'margin-bottom:6px;cursor:pointer;">'
            f'🗓️ 일정 {i+1} 직접 열기 &nbsp;|&nbsp; {fmt(event["start_date"])}'
            f'</button></a>',
            unsafe_allow_html=True,
        )

    # 공유 텍스트 (체크된 것만)
    selected_for_share = [e for e, s in zip(events, share_sels) if s]
    if selected_for_share:
        st.markdown("---")
        st.subheader("📤 공유 링크")
        st.caption("아래 내용을 복사해서 카카오톡 등으로 보내세요.")

        lines = ["📅 일정을 공유합니다\n"]
        for event in selected_for_share:
            lines.append(f"▶ {event.get('title', '')}")
            lines.append(f"  {fmt(event['start_date'])} ~ {fmt(event['end_date'])}")
            if event.get("location"):
                lines.append(f"  📍 {event['location']}")
            if event.get("details"):
                for line in event["details"].splitlines():
                    if line.strip():
                        lines.append(f"  {line}")
            lines.append(f"  🔗 캘린더 바로 추가: {build_calendar_url(event)}")
            lines.append("")

        st.text_area(
            "공유 텍스트",
            value="\n".join(lines),
            height=280,
            label_visibility="collapsed",
        )

    st.markdown("---")
    st.button("새 일정 입력", on_click=clear_all, use_container_width=True)
