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

KO_DAYS = ["월", "화", "수", "목", "금", "토", "일"]

# ── 세션 초기화 ────────────────────────────────────────
for key, default in {
    "input_text": "",
    "events": [],
    "registered": False,
    "auto_open_done": False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ── 유틸 함수 ──────────────────────────────────────────
def validate_gcal_date(date_str):
    return bool(re.match(r"^\d{8}T\d{6}$", str(date_str)))


def fmt(date_str):
    try:
        dt = datetime.strptime(date_str, "%Y%m%dT%H%M%S")
        day_ko = KO_DAYS[dt.weekday()]
        return dt.strftime(f"%m/%d({day_ko}) %H:%M")
    except Exception:
        return date_str


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


def clear_all():
    st.session_state.input_text = ""
    st.session_state.events = []
    st.session_state.registered = False
    st.session_state.auto_open_done = False


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
    st.caption("내용이 틀렸으면 [수정]을 눌러 구글 캘린더에서 직접 수정하세요.")

    # ── 등록된 일정 카드 ──────────────────────────────
    for i, event in enumerate(events):
        with st.container(border=True):
            left, right = st.columns([5, 1])
            with left:
                st.markdown(f"**{event.get('title', '')}**")
                st.markdown(f"📅 &nbsp;{fmt(event['start_date'])} ~ {fmt(event['end_date'])}")
                if event.get("location"):
                    st.markdown(f"📍 &nbsp;{event['location']}")
                if event.get("details"):
                    with st.expander("📝 메모"):
                        st.text(event["details"])
            with right:
                url = build_calendar_url(event)
                st.markdown(
                    f'<a href="{url}" target="_blank">'
                    f'<button style="background:#EA4335;color:white;padding:8px 12px;'
                    f'border:none;border-radius:6px;font-size:13px;font-weight:bold;'
                    f'cursor:pointer;margin-top:12px;">수정</button></a>',
                    unsafe_allow_html=True,
                )

    # 팝업 차단 대비
    with st.expander("팝업이 차단된 경우 여기를 누르세요"):
        for i, event in enumerate(events):
            url = build_calendar_url(event)
            st.markdown(
                f'<a href="{url}" target="_blank">'
                f'<button style="width:100%;background:#34A853;color:white;padding:10px;'
                f'border:none;border-radius:8px;font-size:14px;font-weight:bold;'
                f'margin-bottom:6px;cursor:pointer;">🗓️ 일정 {i+1} 직접 열기</button></a>',
                unsafe_allow_html=True,
            )

    # ── 공유 영역 (완전 클라이언트 사이드) ───────────────
    st.markdown("---")
    st.subheader("📤 공유하기")

    # 공유용 이벤트 데이터 (제목/날짜/장소만)
    share_events = json.dumps([
        {
            "title": e.get("title", ""),
            "date": f"{fmt(e['start_date'])} ~ {fmt(e['end_date'])}",
            "location": e.get("location", ""),
        }
        for e in events
    ], ensure_ascii=False)

    component_height = 80 + len(events) * 64 + 100

    share_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding: 4px 2px; }}
  .item {{
    display: flex; align-items: center;
    padding: 10px 6px; border-bottom: 1px solid #eee;
  }}
  .item input[type=checkbox] {{
    width: 20px; height: 20px; margin-right: 12px;
    cursor: pointer; flex-shrink: 0; accent-color: #4285F4;
  }}
  .item label {{ font-size: 14px; line-height: 1.5; cursor: pointer; }}
  .item label .sub {{ font-size: 12px; color: #888; }}
  .kakao-btn {{
    display: block; width: 100%; margin-top: 14px;
    background: #FEE500; color: #3C1E1E;
    padding: 14px; border: none; border-radius: 8px;
    font-size: 16px; font-weight: bold; cursor: pointer;
    letter-spacing: -0.3px;
  }}
  #msg {{
    margin-top: 10px; font-size: 13px; color: #555;
    white-space: pre-wrap; line-height: 1.6;
  }}
</style>
</head>
<body>
<div id="list"></div>
<button class="kakao-btn" onclick="doShare()">💬 카카오톡으로 공유하기</button>
<p id="msg"></p>
<script>
var events = {share_events};

var list = document.getElementById('list');
events.forEach(function(e, i) {{
  var div = document.createElement('div');
  div.className = 'item';
  div.innerHTML =
    '<input type="checkbox" id="c' + i + '" checked>' +
    '<label for="c' + i + '">' + e.title +
    '<br><span class="sub">' + e.date +
    (e.location ? ' · ' + e.location : '') +
    '</span></label>';
  list.appendChild(div);
}});

async function doShare() {{
  var lines = ['📅 일정 공유\\n'];
  var hasSelected = false;
  events.forEach(function(e, i) {{
    if (document.getElementById('c' + i).checked) {{
      hasSelected = true;
      lines.push(e.title);
      lines.push('📅 ' + e.date);
      if (e.location) lines.push('📍 ' + e.location);
      lines.push('');
    }}
  }});

  if (!hasSelected) {{
    document.getElementById('msg').textContent = '⚠️ 공유할 일정을 선택해 주세요.';
    return;
  }}

  var text = lines.join('\\n').trim();

  /* 1순위: Web Share API (안드로이드 네이티브 공유창 → 카카오톡 선택 가능) */
  if (navigator.share) {{
    try {{
      await navigator.share({{ text: text }});
      document.getElementById('msg').textContent = '';
      return;
    }} catch(e) {{
      if (e.name === 'AbortError') return;
    }}
  }}

  /* 2순위: 클립보드 복사 */
  try {{
    await navigator.clipboard.writeText(text);
    document.getElementById('msg').textContent =
      '✅ 클립보드에 복사됐습니다!\\n카카오톡을 열고 붙여넣기 하세요.';
  }} catch(e) {{
    document.getElementById('msg').textContent =
      '아래 내용을 직접 복사하세요:\\n\\n' + text;
  }}
}}
</script>
</body>
</html>
"""

    components.html(share_html, height=component_height)

    st.markdown("---")
    st.button("새 일정 입력", on_click=clear_all, use_container_width=True)
