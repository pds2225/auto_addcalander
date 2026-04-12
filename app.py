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
    "registered": False,
    "auto_open_done": False,
    "kakao_url": None,
    "share_warning": False,
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


def on_share_click():
    """공유 버튼 콜백 – 선택된 일정으로 카카오톡 URL 생성"""
    events = st.session_state.events
    selected = [
        e for i, e in enumerate(events)
        if st.session_state.get(f"share_{i}", False)
    ]
    if not selected:
        st.session_state.share_warning = True
        st.session_state.kakao_url = None
        return

    st.session_state.share_warning = False
    lines = ["📅 일정 공유\n"]
    for e in selected:
        lines.append(e.get("title", ""))
        lines.append(f"📅 {fmt(e['start_date'])} ~ {fmt(e['end_date'])}")
        if e.get("location"):
            lines.append(f"📍 {e['location']}")
        lines.append("")

    share_text = "\n".join(lines).strip()
    st.session_state.kakao_url = (
        f"kakaotalk://msg/send?text={urllib.parse.quote(share_text)}"
    )


def clear_all():
    st.session_state.input_text = ""
    st.session_state.events = []
    st.session_state.registered = False
    st.session_state.auto_open_done = False
    st.session_state.kakao_url = None
    st.session_state.share_warning = False
    # 체크박스 초기화
    for i in range(20):
        st.session_state.pop(f"share_{i}", None)


# ══════════════════════════════════════════════════════
# 입력 영역
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
                st.session_state.registered = True
                st.session_state.auto_open_done = False
                st.session_state.kakao_url = None
                st.session_state.share_warning = False
            except Exception as e:
                st.error("처리 중 오류가 발생했습니다. 텍스트를 다시 확인해 주세요.")
                st.write(e)
    else:
        st.warning("텍스트를 입력해 주세요.")


# ══════════════════════════════════════════════════════
# 등록 결과 영역
# ══════════════════════════════════════════════════════
if st.session_state.registered and st.session_state.events:
    events = st.session_state.events

    # 최초 1회 구글 캘린더 탭 자동 오픈
    if not st.session_state.auto_open_done:
        urls = [build_calendar_url(e) for e in events]
        js_opens = "\n".join([f'window.open("{u}", "_blank");' for u in urls])
        components.html(f"<script>{js_opens}</script>", height=1)
        st.session_state.auto_open_done = True

    st.markdown("---")
    st.success(f"✅ {len(events)}개 일정 등록 완료!")
    st.caption("내용이 틀렸으면 [수정하기]를 눌러 구글 캘린더에서 직접 수정하세요.")

    # ── 등록된 일정 카드 ──────────────────────────────
    for i, event in enumerate(events):
        with st.container(border=True):
            left, right = st.columns([5, 1])
            with left:
                st.markdown(f"**{event.get('title', '')}**")
                st.markdown(f"📅 &nbsp; {fmt(event['start_date'])} ~ {fmt(event['end_date'])}")
                if event.get("location"):
                    st.markdown(f"📍 &nbsp; {event['location']}")
                if event.get("details"):
                    with st.expander("📝 메모"):
                        st.text(event["details"])
            with right:
                url = build_calendar_url(event)
                st.markdown(
                    f'<a href="{url}" target="_blank">'
                    f'<button style="background:#EA4335;color:white;'
                    f'padding:8px 12px;border:none;border-radius:6px;'
                    f'font-size:13px;font-weight:bold;cursor:pointer;margin-top:12px;">'
                    f'수정</button></a>',
                    unsafe_allow_html=True,
                )

    # 팝업 차단 대비
    with st.expander("팝업이 차단된 경우 여기를 누르세요"):
        for i, event in enumerate(events):
            url = build_calendar_url(event)
            st.markdown(
                f'<a href="{url}" target="_blank">'
                f'<button style="width:100%;background:#34A853;color:white;'
                f'padding:10px;border:none;border-radius:8px;font-size:14px;'
                f'font-weight:bold;margin-bottom:6px;cursor:pointer;">'
                f'🗓️ 일정 {i+1} 직접 열기</button></a>',
                unsafe_allow_html=True,
            )

    # ── 공유 영역 ─────────────────────────────────────
    st.markdown("---")
    st.subheader("📤 공유하기")
    st.caption("공유할 일정을 선택하세요.")

    for i, event in enumerate(events):
        label = f"일정 {i+1}  ·  {fmt(event['start_date'])}  ·  {event.get('title', '')}"
        st.checkbox(label, key=f"share_{i}", value=False)

    st.button(
        "공유 일정 선택 완료",
        on_click=on_share_click,
        use_container_width=True,
    )

    if st.session_state.share_warning:
        st.warning("공유할 일정을 1개 이상 선택해 주세요.")

    # 카카오톡 버튼: 공유 선택 완료 후 표시
    if st.session_state.kakao_url:
        st.markdown(
            f'<a href="{st.session_state.kakao_url}">'
            f'<button style="width:100%;background:#FEE500;color:#3C1E1E;'
            f'padding:15px;border:none;border-radius:8px;font-size:16px;'
            f'font-weight:bold;cursor:pointer;margin-top:4px;">'
            f'💬 카카오톡으로 공유하기</button></a>',
            unsafe_allow_html=True,
        )
        st.caption("카카오톡이 열리면 받는 사람을 선택해서 보내세요.")

    st.markdown("---")
    st.button("새 일정 입력", on_click=clear_all, use_container_width=True)
