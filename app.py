import streamlit as st
import os
import json
import datetime
import calendar
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
from PIL import Image
import platform

# OS별 시스템 한글 폰트 설정 (koreanize-matplotlib 없이 작동)
system_os = platform.system()
from matplotlib import font_manager

ko_font_prop = None
if system_os == "Windows":
    plt.rc('font', family='Malgun Gothic')
elif system_os == "Darwin": # macOS
    plt.rc('font', family='AppleGothic')
else: # Linux / Streamlit Cloud
    # 나눔고딕 파일 경로 직접 탐색 (캐시 꼬임 방지)
    nanum_paths = [
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
        "/usr/share/fonts/nanum/NanumGothic.ttf"
    ]
    for path in nanum_paths:
        if os.path.exists(path):
            ko_font_prop = font_manager.FontProperties(fname=path)
            break
            
    if ko_font_prop is not None:
        try:
            # matplotlib에 직접 폰트 파일 등록
            font_manager.fontManager.addfont(ko_font_prop.get_file())
            plt.rc('font', family=ko_font_prop.get_name())
        except Exception:
            plt.rc('font', family='NanumGothic')
    else:
        plt.rc('font', family='NanumGothic')

# 마이너스 기호 깨짐 방지
plt.rc('axes', unicode_minus=False)

# 이모티콘 폰트 설정
emoji_font_prop = None
if system_os == "Windows":
    try:
        emoji_font_prop = font_manager.FontProperties(fname="C:\\Windows\\Fonts\\seguiemj.ttf")
    except Exception:
        emoji_font_prop = font_manager.FontProperties(family="Segoe UI Emoji")
elif system_os == "Darwin":
    emoji_font_prop = font_manager.FontProperties(family="Apple Color Emoji")
else: # Linux / Streamlit Cloud
    emoji_paths = [
        "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
        "/usr/share/fonts/truetype/noto-emoji/NotoColorEmoji.ttf"
    ]
    for path in emoji_paths:
        if os.path.exists(path):
            emoji_font_prop = font_manager.FontProperties(fname=path)
            break
    if emoji_font_prop is None:
        emoji_font_prop = font_manager.FontProperties(family="Noto Color Emoji")

def is_emoji(char):
    code = ord(char)
    return (
        0x1F600 <= code <= 0x1F64F or
        0x1F300 <= code <= 0x1F5FF or
        0x1F680 <= code <= 0x1F6FF or
        0x2600 <= code <= 0x26FF or
        0x2700 <= code <= 0x27BF or
        0xFE00 <= code <= 0xFE0F or
        0x1F900 <= code <= 0x1F9FF or
        0x1F1E6 <= code <= 0x1F1FF or
        code > 0xFFFF
    )

def draw_mixed_text_mpl(ax, x, y, text, fontsize, color, emoji_font, ha='left', va='bottom', fontweight='normal', style='normal'):
    """
    matplotlib axes 상에서 이모티콘과 한글/영문 텍스트가 섞여 있을 때,
    각 문자의 폰트를 구별하여 겹침 및 깨짐 없이 렌더링합니다.
    """
    # 14x11 인치 피규어 기준, transAxes 상에서의 가로 비율(Axes 가로 90%)
    axes_width_inches = 14.0 * 0.90
    
    chars_info = []
    total_width = 0.0
    
    for char in text:
        is_em = is_emoji(char)
        if is_em:
            w = (fontsize / 72.0) / axes_width_inches * 1.15
        elif ord(char) < 128:
            w = (fontsize / 72.0) / axes_width_inches * 0.55
        else:
            w = (fontsize / 72.0) / axes_width_inches * 1.0
        chars_info.append((char, is_em, w))
        total_width += w
        
    start_x = x
    if ha == 'center':
        start_x = x - total_width / 2.0
    elif ha == 'right':
        start_x = x - total_width
        
    current_x = start_x
    for char, is_em, w in chars_info:
        if is_em:
            ax.text(current_x, y, char, fontproperties=emoji_font, fontsize=fontsize, color=color,
                    ha='left', va=va, transform=ax.transAxes, zorder=3)
        else:
            ax.text(current_x, y, char, fontsize=fontsize, color=color,
                    ha='left', va=va, transform=ax.transAxes, zorder=3,
                    weight=fontweight, style=style)
        current_x += w



# ==========================================
# 1. 초기 상 설정 및 디렉토리 관리
# ==========================================
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)
LAST_ACTIVE_PATH = os.path.join(DATA_DIR, "last_active.json")

# 이모티콘 정의
EMOTIONS = ["선택 안 함", "😀 행복", "😐 보통", "😢 슬픔", "😡 분노", "😴 피곤", "💖 설렘", "😎 신남", "🥳 축하", "🥺 우울"]
WEATHER = ["선택 안 함", "☀️ 맑음", "☁️ 흐림", "🌧 비", "⛈ 번개", "❄️ 눈", "💨 바람", "🌫 안개"]
STICKERS = ["⭐", "❤️", "🎉", "🌱", "📚", "✈️", "🎂", "🍀", "💡", "🔍"]

# 테마 정의
THEMES = {
    "파스텔 핑크": {
        "bg": "#FFF5F5",
        "header": "#FFC0CB",
        "cell": "#FFFFFF",
        "text": "#4A4A4A",
        "accent": "#FF8DA1",
        "border": "#FFE4E1"
    },
    "파스텔 뱅쇼 (라벤더)": {
        "bg": "#F9F0FF",
        "header": "#E1BEE7",
        "cell": "#FFFFFF",
        "text": "#4A3B52",
        "accent": "#BA68C8",
        "border": "#F3E5F5"
    },
    "파스텔 블루": {
        "bg": "#F0F8FF",
        "header": "#B0C4DE",
        "cell": "#FFFFFF",
        "text": "#4A4A4A",
        "accent": "#4682B4",
        "border": "#E6F2FF"
    },
    "민트": {
        "bg": "#E8F8F5",
        "header": "#A3E4D7",
        "cell": "#FFFFFF",
        "text": "#2C3E50",
        "accent": "#16A085",
        "border": "#D1F2EB"
    }
}

DARK_THEME = {
    "bg": "#1E1E1E",
    "header": "#333333",
    "cell": "#2D2D2D",
    "text": "#E0E0E0",
    "accent": "#BB86FC",
    "border": "#444444"
}

# ==========================================
# 2. 데이터 파일 CRUD 함수 정의
# ==========================================
def get_calendar_filename(calendar_id):
    # 안전한 파일 이름 변환
    safe_id = "".join([c if c.isalnum() or c in ("-", "_") else "_" for c in calendar_id])
    return os.path.join(DATA_DIR, f"cal_{safe_id}.json")

def save_calendar(calendar_data):
    filename = get_calendar_filename(calendar_data["id"])
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(calendar_data, f, ensure_ascii=False, indent=2)

def load_calendar(calendar_id):
    filename = get_calendar_filename(calendar_id)
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def delete_calendar(calendar_id):
    filename = get_calendar_filename(calendar_id)
    if os.path.exists(filename):
        os.remove(filename)
    # 마지막 활성 달력 리셋
    if load_last_active_id() == calendar_id:
        save_last_active_id("")

def list_calendars():
    calendars_list = []
    for file in os.listdir(DATA_DIR):
        if file.startswith("cal_") and file.endswith(".json"):
            filepath = os.path.join(DATA_DIR, file)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    calendars_list.append({
                        "id": data.get("id"),
                        "name": data.get("name"),
                        "year": data.get("year"),
                        "month": data.get("month")
                    })
            except Exception:
                pass
    return calendars_list

def save_last_active_id(calendar_id):
    with open(LAST_ACTIVE_PATH, "w", encoding="utf-8") as f:
        json.dump({"last_active_id": calendar_id}, f, ensure_ascii=False)

def load_last_active_id():
    if os.path.exists(LAST_ACTIVE_PATH):
        try:
            with open(LAST_ACTIVE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("last_active_id", "")
        except Exception:
            pass
    return ""

def create_default_calendar(calendar_id, name, year, month):
    return {
        "id": calendar_id,
        "name": name,
        "year": year,
        "month": month,
        "theme_name": "파스텔 핑크",
        "custom_colors": {
            "bg": "#FFF5F5",
            "header": "#FFC0CB",
            "cell": "#FFFFFF",
            "text": "#4A4A4A",
            "accent": "#FF8DA1",
            "border": "#FFE4E1"
        },
        "days": {}  # 예: "1": {"memo": "", "emotion": "선택 안 함", "weather": "선택 안 함", "stickers": []}
    }

# ==========================================
# 3. Streamlit 앱 초기화
# ==========================================
st.set_page_config(
    page_title="몽글몽글 감성 다이어리 달력",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if "current_calendar_id" not in st.session_state:
    last_id = load_last_active_id()
    all_cals = list_calendars()
    
    if last_id and any(c["id"] == last_id for c in all_cals):
        st.session_state.current_calendar_id = last_id
    elif all_cals:
        st.session_state.current_calendar_id = all_cals[0]["id"]
    else:
        # 최초 실행 시 기본 달력 하나 생성
        now = datetime.datetime.now()
        default_id = f"diary_{now.year}_{now.month}"
        default_name = f"{now.year}년 {now.month}월 다이어리"
        default_cal = create_default_calendar(default_id, default_name, now.year, now.month)
        save_calendar(default_cal)
        save_last_active_id(default_id)
        st.session_state.current_calendar_id = default_id

# 현재 달력 데이터 로드
current_data = load_calendar(st.session_state.current_calendar_id)
if current_data is None:
    # 예외 상황 처리: 만약 삭제되었거나 파일이 없을 경우
    all_cals = list_calendars()
    if all_cals:
        st.session_state.current_calendar_id = all_cals[0]["id"]
        current_data = load_calendar(st.session_state.current_calendar_id)
    else:
        now = datetime.datetime.now()
        default_id = f"diary_{now.year}_{now.month}"
        default_name = f"{now.year}년 {now.month}월 다이어리"
        current_data = create_default_calendar(default_id, default_name, now.year, now.month)
        save_calendar(current_data)
        st.session_state.current_calendar_id = default_id

st.session_state.calendar_data = current_data

# ==========================================
# 4. 다크 모드 및 테마 CSS 설정
# ==========================================
# 사이드바 상단에 다크 모드 토글 배치
is_dark = st.sidebar.toggle("🌙 다크 모드 활성화", value=False)

# 테마 색상 획득
theme_name = st.session_state.calendar_data.get("theme_name", "파스텔 핑크")
if is_dark:
    colors = DARK_THEME
else:
    if theme_name == "사용자 지정":
        colors = st.session_state.calendar_data.get("custom_colors", THEMES["파스텔 핑크"])
    else:
        colors = THEMES.get(theme_name, THEMES["파스텔 핑크"])

# CSS 주입 (감성 폰트, 둥글둥글 카드 스타일, 테마 색상 동적 바인딩)
custom_css = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Gowun+Dodum&display=swap');

html, body, [data-testid="stAppViewContainer"], .st-emotion-cache-12fmwja, .st-key-calendar_view {{
    font-family: 'Gowun Dodum', sans-serif !important;
    background-color: {colors['bg']} !important;
    color: {colors['text']} !important;
}}

/* 사이드바 스타일링 */
[data-testid="stSidebar"] {{
    background-color: {colors['cell']} !important;
    border-right: 2px dashed {colors['header']} !important;
}}

/* 헤더 제목 스타일링 */
.diary-title {{
    font-size: 2.2rem;
    font-weight: bold;
    color: {colors['accent']};
    text-align: center;
    margin-bottom: 5px;
    text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
}}

.diary-subtitle {{
    font-size: 1.1rem;
    color: {colors['text']};
    text-align: center;
    margin-bottom: 25px;
    font-style: italic;
}}

/* 달력 그리드 스타일 */
.calendar-grid-header {{
    background-color: {colors['header']} !important;
    color: {colors['text']} !important;
    font-weight: bold;
    text-align: center;
    padding: 10px;
    border-radius: 8px;
    margin-bottom: 10px;
    box-shadow: 0px 2px 5px rgba(0,0,0,0.05);
}}

.calendar-day-card {{
    background-color: {colors['cell']} !important;
    border: 1px solid {colors['border']} !important;
    border-radius: 12px;
    padding: 12px;
    min-height: 140px;
    position: relative;
    box-shadow: 2px 2px 8px rgba(0,0,0,0.03);
    transition: transform 0.2s, box-shadow 0.2s;
}}

.calendar-day-card:hover {{
    transform: translateY(-2px);
    box-shadow: 3px 5px 12px rgba(0,0,0,0.06);
    border-color: {colors['accent']} !important;
}}

.day-number {{
    font-size: 1.2rem;
    font-weight: bold;
    color: {colors['text']};
}}

.day-emojis {{
    font-size: 1.1rem;
    margin-top: 5px;
    display: flex;
    gap: 5px;
}}

.day-stickers {{
    font-size: 1.0rem;
    margin-top: 5px;
    letter-spacing: 2px;
}}

.day-memo-preview {{
    font-size: 0.85rem;
    color: {colors['text']};
    opacity: 0.85;
    margin-top: 8px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    border-top: 1px dashed {colors['border']};
    padding-top: 4px;
}}

/* 팝오버 버튼 미세 조정 */
.stPopover button {{
    background-color: transparent !important;
    border: 1px dashed {colors['accent']} !important;
    color: {colors['accent']} !important;
    padding: 2px 8px !important;
    font-size: 0.8rem !important;
    border-radius: 6px !important;
    width: 100% !important;
    margin-top: 8px !important;
}}

.stPopover button:hover {{
    background-color: {colors['header']} !important;
    color: {colors['text']} !important;
}}

/* 메인 저장 버튼 */
.save-btn-container {{
    display: flex;
    justify-content: flex-end;
    margin-bottom: 15px;
}}

/* 달력 통계 스타일 */
.stat-box {{
    background-color: {colors['cell']};
    border: 1px solid {colors['border']};
    border-radius: 12px;
    padding: 15px;
    text-align: center;
    box-shadow: 1px 2px 6px rgba(0,0,0,0.02);
}}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ==========================================
# 5. 사이드바 제어 로직 (달력 관리 및 커스터마이징)
# ==========================================
st.sidebar.markdown(f"<h3 style='color:{colors['accent']}; font-weight:bold;'>📂 내 다이어리 목록</h3>", unsafe_allow_html=True)

# 모든 달력 목록 로드
all_calendars = list_calendars()
cal_options = {c["id"]: f"{c['name']} ({c['year']}년 {c['month']}월)" for c in all_calendars}

# 달력 선택 selectbox
selected_cal_id = st.sidebar.selectbox(
    "열어볼 달력을 선택하세요",
    options=list(cal_options.keys()),
    format_func=lambda x: cal_options[x],
    index=list(cal_options.keys()).index(st.session_state.current_calendar_id) if st.session_state.current_calendar_id in cal_options else 0
)

# 달력이 변경되면 상태 업데이트
if selected_cal_id != st.session_state.current_calendar_id:
    st.session_state.current_calendar_id = selected_cal_id
    save_last_active_id(selected_cal_id)
    st.rerun()

# -----------------
# 5-1. 새 달력 생성 버튼
# -----------------
st.sidebar.markdown("---")
st.sidebar.markdown(f"<h4 style='color:{colors['accent']};'>✨ 새 달력 만들기</h4>", unsafe_allow_html=True)

with st.sidebar.expander("➕ 새로운 다이어리 달력 추가", expanded=False):
    new_cal_name = st.text_input("달력 이름", placeholder="예: 2026년 여름 휴가 계획", key="new_name")
    
    now_dt = datetime.datetime.now()
    new_cal_year = st.selectbox("연도 선택", list(range(now_dt.year - 5, now_dt.year + 6)), index=5)
    new_cal_month = st.selectbox("월 선택", list(range(1, 13)), index=now_dt.month - 1)
    
    create_btn = st.button("달력 생성 및 열기", use_container_width=True)
    if create_btn:
        if not new_cal_name.strip():
            st.error("달력 이름을 입력해주세요!")
        else:
            new_id = f"diary_{new_cal_year}_{new_cal_month}_{int(datetime.datetime.now().timestamp())}"
            new_cal_data = create_default_calendar(new_id, new_cal_name, new_cal_year, new_cal_month)
            save_calendar(new_cal_data)
            
            st.session_state.current_calendar_id = new_id
            save_last_active_id(new_id)
            st.success("새 달력이 생성되었습니다!")
            st.rerun()

# -----------------
# 5-2. 달력 삭제 기능
# -----------------
st.sidebar.markdown("---")
st.sidebar.markdown(f"<h4 style='color:#E57373;'>🗑️ 다이어리 삭제</h4>", unsafe_allow_html=True)

with st.sidebar.expander("⚠️ 달력 삭제하기", expanded=False):
    st.warning("달력을 삭제하면 기록된 모든 일정과 꾸미기 정보가 영구히 소실됩니다.")
    delete_confirm = st.text_input("삭제하려면 '삭제'라고 입력하세요", placeholder="삭제")
    delete_btn = st.button("현재 달력 삭제", type="primary", use_container_width=True)
    
    if delete_btn:
        if delete_confirm == "삭제":
            delete_calendar(st.session_state.current_calendar_id)
            st.success("달력이 정상적으로 삭제되었습니다.")
            st.rerun()
        else:
            st.error("입력값이 일치하지 않습니다. '삭제'를 정확히 입력해주세요.")

# -----------------
# 5-3. 테마 및 데코레이션 설정 (사이드바)
# -----------------
st.sidebar.markdown("---")
st.sidebar.markdown(f"<h4 style='color:{colors['accent']};'>🎨 달력 테마 설정</h4>", unsafe_allow_html=True)

# 테마 선택
theme_list = list(THEMES.keys()) + ["사용자 지정"]
default_theme_idx = theme_list.index(theme_name) if theme_name in theme_list else 0

selected_theme = st.sidebar.selectbox(
    "테마 스타일",
    options=theme_list,
    index=default_theme_idx
)

# 사용자 지정 테마일 경우 컬러 피커들 제공
custom_colors = st.session_state.calendar_data.get("custom_colors", THEMES["파스텔 핑크"])
if selected_theme == "사용자 지정":
    col_bg = st.sidebar.color_picker("전체 배경색", custom_colors.get("bg", "#FFF5F5"))
    col_hdr = st.sidebar.color_picker("헤더 색상", custom_colors.get("header", "#FFC0CB"))
    col_cell = st.sidebar.color_picker("날짜 칸 색상", custom_colors.get("cell", "#FFFFFF"))
    col_txt = st.sidebar.color_picker("글자 색상", custom_colors.get("text", "#4A4A4A"))
    col_acc = st.sidebar.color_picker("강조 테두리 색상", custom_colors.get("accent", "#FF8DA1"))
    col_brd = st.sidebar.color_picker("날짜 칸 테두리 색상", custom_colors.get("border", "#FFE4E1"))
    
    custom_colors = {
        "bg": col_bg,
        "header": col_hdr,
        "cell": col_cell,
        "text": col_txt,
        "accent": col_acc,
        "border": col_brd
    }

# 사이드바 하단 테마 임시 적용 확인용
theme_apply_btn = st.sidebar.button("테마 색상 즉시 적용", use_container_width=True)
if theme_apply_btn:
    st.session_state.calendar_data["theme_name"] = selected_theme
    if selected_theme == "사용자 지정":
        st.session_state.calendar_data["custom_colors"] = custom_colors
    save_calendar(st.session_state.calendar_data)
    st.rerun()

# ==========================================
# 6. 메인 화면 렌더링
# ==========================================

# 상단 제목 영역
st.markdown(f"<div class='diary-title'>🧸 몽글몽글 감성 다이어리 달력</div>", unsafe_allow_html=True)
st.markdown(f"<div class='diary-subtitle'>소중한 순간, 하루하루의 감정과 일정을 다이어리에 기록해보세요.</div>", unsafe_allow_html=True)

# 현재 달력 메타데이터
cal_name = st.session_state.calendar_data.get("name")
cal_year = st.session_state.calendar_data.get("year")
cal_month = st.session_state.calendar_data.get("month")

# 메인 헤더 & 상태 저장 버튼 레이아웃
header_col1, header_col2 = st.columns([3, 1])
with header_col1:
    st.markdown(f"### 📖 **{cal_name}** ({cal_year}년 {cal_month}월)")
with header_col2:
    save_clicked = st.button("💾 다이어리 영구 저장", type="primary", use_container_width=True)
    if save_clicked:
        save_calendar(st.session_state.calendar_data)
        st.success("🎉 다이어리가 안전하게 저장되었습니다!")

# 탭 설정: [📅 달력 꾸미기, 📊 월별 통계 분석, ⚙️ 사진 앨범 & 내보내기]
tab_cal, tab_stats, tab_export = st.tabs(["📅 달력 꾸미기", "📊 월별 통계 분석", "⚙️ 내보내기 및 관리"])

# -----------------
# 6-1. 달력 꾸미기 탭
# -----------------
with tab_cal:
    # 달력 날짜 계산 (일요일 시작)
    cal_obj = calendar.Calendar(firstweekday=6) # 6 = Sunday
    weeks = cal_obj.monthdayscalendar(cal_year, cal_month)
    
    # 요일 헤더 표시
    weekdays_ko = ["일", "월", "화", "수", "목", "금", "토"]
    cols_header = st.columns(7)
    for idx, day_ko in enumerate(weekdays_ko):
        # 일요일은 빨간색 톤, 토요일은 파란색 톤, 평일은 기본 텍스트 색 톤으로 감성 표현
        if idx == 0:
            color_style = "color: #E57373;"
        elif idx == 6:
            color_style = "color: #64B5F6;"
        else:
            color_style = f"color: {colors['text']};"
            
        cols_header[idx].markdown(
            f"<div class='calendar-grid-header' style='{color_style}'>{day_ko}요일</div>", 
            unsafe_allow_html=True
        )
    
    # 주차별 날짜 카드 렌더링
    for week_idx, week in enumerate(weeks):
        cols_day = st.columns(7)
        for day_idx, day in enumerate(week):
            if day == 0:
                # 이전/다음 달에 해당하는 빈 칸
                cols_day[day_idx].markdown(
                    f"<div style='min-height: 140px; border: 1px dashed {colors['border']}; border-radius: 12px; opacity: 0.2;'></div>", 
                    unsafe_allow_html=True
                )
            else:
                day_str = str(day)
                # 날짜 데이터 초기화
                if day_str not in st.session_state.calendar_data["days"]:
                    st.session_state.calendar_data["days"][day_str] = {
                        "memo": "",
                        "emotion": "선택 안 함",
                        "weather": "선택 안 함",
                        "stickers": []
                    }
                
                day_info = st.session_state.calendar_data["days"][day_str]
                memo = day_info.get("memo", "")
                emotion = day_info.get("emotion", "선택 안 함")
                weather = day_info.get("weather", "선택 안 함")
                stickers = day_info.get("stickers", [])
                
                # 요일별 날짜 숫자 색상 설정
                if day_idx == 0: # 일요일
                    num_color = "#E57373"
                elif day_idx == 6: # 토요일
                    num_color = "#64B5F6"
                else:
                    num_color = colors['text']
                
                # 카드 내부에 노출될 텍스트 파싱
                emotion_emoji = emotion.split(" ")[0] if emotion != "선택 안 함" else ""
                weather_emoji = weather.split(" ")[0] if weather != "선택 안 함" else ""
                stickers_str = "".join(stickers)
                memo_preview = memo.split("\n")[0] if memo else ""
                
                # 날짜 칸 카드 렌더링
                card_html = f"""
                <div class='calendar-day-card'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <span class='day-number' style='color: {num_color};'>{day}</span>
                        <div class='day-emojis'>
                            <span>{emotion_emoji}</span>
                            <span>{weather_emoji}</span>
                        </div>
                    </div>
                    <div class='day-stickers'>{stickers_str}</div>
                    <div class='day-memo-preview'>{memo_preview if memo_preview else "<span style='opacity:0.3;'>메모 없음</span>"}</div>
                </div>
                """
                cols_day[day_idx].markdown(card_html, unsafe_allow_html=True)
                
                # 각 칸 하단에 팝오버를 두어 일정/이모티콘/스티커 수정
                with cols_day[day_idx]:
                    with st.popover("✏️ 기록", use_container_width=True):
                        st.markdown(f"#### 📅 {cal_year}년 {cal_month}월 {day}일 기록")
                        
                        # 1. 일정/메모 입력
                        new_memo = st.text_area("일정 및 메모 (여러 줄 입력 가능)", value=memo, key=f"memo_{day_str}", height=100)
                        
                        pop_col1, pop_col2 = st.columns(2)
                        with pop_col1:
                            # 2. 감정 이모티콘 선택
                            default_emo_idx = EMOTIONS.index(emotion) if emotion in EMOTIONS else 0
                            new_emotion = st.selectbox("오늘의 감정", EMOTIONS, index=default_emo_idx, key=f"emo_{day_str}")
                        with pop_col2:
                            # 3. 날씨 이모티콘 선택
                            default_wea_idx = WEATHER.index(weather) if weather in WEATHER else 0
                            new_weather = st.selectbox("오늘의 날씨", WEATHER, index=default_wea_idx, key=f"wea_{day_str}")
                        
                        # 4. 스티커 부착
                        new_stickers = st.multiselect("달력 스티커 부착", STICKERS, default=stickers, key=f"stk_{day_str}")
                        
                        # 변경 시 세션 상태에 즉시 동기화
                        st.session_state.calendar_data["days"][day_str] = {
                            "memo": new_memo,
                            "emotion": new_emotion,
                            "weather": new_weather,
                            "stickers": new_stickers
                        }
                        
                        # 팝오버 내 변경이 감지되면 재렌더링하여 화면 갱신
                        if (new_memo != memo or new_emotion != emotion or new_weather != weather or new_stickers != stickers):
                            save_calendar(st.session_state.calendar_data)
                            st.rerun()

# -----------------
# 6-2. 월별 통계 분석 탭
# -----------------
with tab_stats:
    st.markdown(f"### 📊 **{cal_name}** 감정 & 날씨 기록 통계")
    
    # 데이터 집계
    days_data = st.session_state.calendar_data.get("days", {})
    emotion_counts = {}
    weather_counts = {}
    total_entries = 0
    
    for d, info in days_data.items():
        memo = info.get("memo", "")
        emo = info.get("emotion", "선택 안 함")
        wea = info.get("weather", "선택 안 함")
        
        # 실제 기록이 존재하는 경우만 수집
        if memo or emo != "선택 안 함" or wea != "선택 안 함":
            total_entries += 1
            if emo != "선택 안 함":
                emotion_counts[emo] = emotion_counts.get(emo, 0) + 1
            if wea != "선택 안 함":
                weather_counts[wea] = weather_counts.get(wea, 0) + 1
                
    if total_entries == 0:
        st.info("아직 달력에 기록된 일정이나 감정/날씨 정보가 없습니다. [달력 꾸미기] 탭에서 오늘의 상태를 기록해보세요!")
    else:
        # 요약 카드 출력
        stat_col1, stat_col2, stat_col3 = st.columns(3)
        
        # 가장 흔한 감정 계산
        most_common_emo = max(emotion_counts, key=emotion_counts.get) if emotion_counts else "기록 없음"
        most_common_wea = max(weather_counts, key=weather_counts.get) if weather_counts else "기록 없음"
        
        with stat_col1:
            st.markdown(f"""
            <div class='stat-box'>
                <h4 style='color:{colors['accent']}; margin-bottom: 5px;'>📅 총 기록 일수</h4>
                <p style='font-size: 2.2rem; font-weight: bold; margin: 0;'>{total_entries} 일</p>
                <small style='color:#777;'>한 달 중 {total_entries}일 동안 다이어리를 썼어요.</small>
            </div>
            """, unsafe_allow_html=True)
            
        with stat_col2:
            st.markdown(f"""
            <div class='stat-box'>
                <h4 style='color:{colors['accent']}; margin-bottom: 5px;'>🌈 이번 달 대표 감정</h4>
                <p style='font-size: 2.2rem; font-weight: bold; margin: 0;'>{most_common_emo.split(' ')[0] if most_common_emo != '기록 없음' else '🎈'}</p>
                <small style='color:#777;'>{most_common_emo if most_common_emo != '기록 없음' else '감정 기록이 없어요'}</small>
            </div>
            """, unsafe_allow_html=True)
            
        with stat_col3:
            st.markdown(f"""
            <div class='stat-box'>
                <h4 style='color:{colors['accent']}; margin-bottom: 5px;'>🌤️ 이번 달 대표 날씨</h4>
                <p style='font-size: 2.2rem; font-weight: bold; margin: 0;'>{most_common_wea.split(' ')[0] if most_common_wea != '기록 없음' else '🍀'}</p>
                <small style='color:#777;'>{most_common_wea if most_common_wea != '기록 없음' else '날씨 기록이 없어요'}</small>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 그래프 드로잉
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            if emotion_counts:
                st.markdown("##### 🧸 감정 분포")
                emo_df = pd.DataFrame(list(emotion_counts.items()), columns=["감정", "횟수"]).sort_values(by="횟수", ascending=False)
                st.bar_chart(
                    emo_df,
                    x="감정",
                    y="횟수",
                    color=colors['accent'],
                    use_container_width=True
                )
            else:
                st.info("아직 분석할 감정 통계 데이터가 부족합니다.")
                
        with chart_col2:
            if weather_counts:
                st.markdown("##### ☀️ 날씨 분포")
                wea_df = pd.DataFrame(list(weather_counts.items()), columns=["날씨", "횟수"]).sort_values(by="횟수", ascending=False)
                st.bar_chart(
                    wea_df,
                    x="날씨",
                    y="횟수",
                    color=colors['header'],
                    use_container_width=True
                )
            else:
                st.info("아직 분석할 날씨 통계 데이터가 부족합니다.")

# ==========================================
# 7. 이미지 및 내보내기 탭 구현
# ==========================================
def draw_calendar_image(cal_data, theme_colors):
    """
    matplotlib을 활용해 실제 폰트 깨짐 없이 달력을 고해상도 이미지로 생성합니다.
    """
    year = cal_data.get("year")
    month = cal_data.get("month")
    name = cal_data.get("name")
    
    cal_obj = calendar.Calendar(firstweekday=6)
    weeks = cal_obj.monthdayscalendar(year, month)
    
    # matplotlib figure 및 axes 설정
    fig, ax = plt.subplots(figsize=(14, 11), dpi=150)
    fig.patch.set_facecolor(theme_colors['bg'])
    ax.set_facecolor(theme_colors['cell'])
    
    # 축 비활성화
    ax.axis('off')
    
    # 1. 제목 그리기
    draw_mixed_text_mpl(ax, 0.5, 0.95, f"📖 {name}", 24, theme_colors['accent'], emoji_font_prop,
                        ha='center', va='center', fontweight='bold')
    draw_mixed_text_mpl(ax, 0.5, 0.91, f"🧸 감정과 일정이 고스란히 담긴 내 디지털 다이어리", 12, theme_colors['text'], emoji_font_prop,
                        ha='center', va='center', style='italic')
    
    # 2. 요일 그리드 헤더
    weekdays = ["일", "월", "화", "수", "목", "금", "토"]
    
    # 그리드 좌표 매핑 계산
    # y축 범위는 0.1 ~ 0.85로 설정하고 x축은 0.05 ~ 0.95로 설정
    col_width = 0.90 / 7
    row_height = 0.73 / len(weeks)
    
    # 요일 헤더 그리기
    for col_idx, day_name in enumerate(weekdays):
        x = 0.05 + col_idx * col_width + col_width / 2
        y = 0.86
        
        # 요일 글자 색상 분기
        if col_idx == 0:
            txt_color = "#E57373"
        elif col_idx == 6:
            txt_color = "#64B5F6"
        else:
            txt_color = theme_colors['text']
            
        # 헤더 배경 박스 그리기
        ax.add_patch(plt.Rectangle((0.05 + col_idx * col_width + 0.003, 0.84), col_width - 0.006, 0.04,
                                   facecolor=theme_colors['header'], edgecolor='none', 
                                   transform=ax.transAxes, zorder=1))
        
        draw_mixed_text_mpl(ax, x, y, f"{day_name}요일", 11, txt_color, emoji_font_prop,
                            ha='center', va='center', fontweight='bold')
        
    # 3. 날짜 칸과 내용 그리기
    for r_idx, week in enumerate(weeks):
        for c_idx, day in enumerate(week):
            # 셀 영역 좌하단 x, y 좌표
            x_box = 0.05 + c_idx * col_width
            # 행은 위에서부터 아래로 내려감 (weeks 역순 렌더링을 위해 변환)
            y_box = 0.82 - (r_idx + 1) * row_height
            
            # 셀 배경 사각형 그리기
            if day == 0:
                # 빈 칸
                ax.add_patch(plt.Rectangle((x_box + 0.003, y_box + 0.003), col_width - 0.006, row_height - 0.006,
                                           facecolor=theme_colors['bg'], edgecolor=theme_colors['border'], linestyle='--',
                                           transform=ax.transAxes, zorder=1))
            else:
                day_str = str(day)
                day_info = cal_data.get("days", {}).get(day_str, {})
                memo = day_info.get("memo", "")
                emotion = day_info.get("emotion", "선택 안 함")
                weather = day_info.get("weather", "선택 안 함")
                stickers = day_info.get("stickers", [])
                
                # 날짜 칸 카드 박스
                ax.add_patch(plt.Rectangle((x_box + 0.003, y_box + 0.003), col_width - 0.006, row_height - 0.006,
                                           facecolor=theme_colors['cell'], edgecolor=theme_colors['border'], linewidth=1.5,
                                           transform=ax.transAxes, zorder=1))
                
                # 날짜 숫자
                num_color = "#E57373" if c_idx == 0 else ("#64B5F6" if c_idx == 6 else theme_colors['text'])
                draw_mixed_text_mpl(ax, x_box + 0.01, y_box + row_height - 0.02, str(day), 13, num_color, emoji_font_prop,
                                    ha='left', va='top', fontweight='bold')
                
                # 감정/날씨 이모티콘 텍스트
                emo_e = emotion.split(" ")[0] if emotion != "선택 안 함" else ""
                wea_e = weather.split(" ")[0] if weather != "선택 안 함" else ""
                emojis_text = f"{emo_e} {wea_e}".strip()
                if emojis_text:
                    draw_mixed_text_mpl(ax, x_box + col_width - 0.01, y_box + row_height - 0.02, emojis_text, 12, theme_colors['text'], emoji_font_prop,
                                        ha='right', va='top')
                
                # 스티커 렌더링
                if stickers:
                    stickers_str = "".join(stickers)
                    draw_mixed_text_mpl(ax, x_box + 0.01, y_box + row_height - 0.045, stickers_str, 10, theme_colors['text'], emoji_font_prop,
                                        ha='left', va='top')
                
                # 메모 미리보기 (최대 3줄 표시 및 개행 문자 처리)
                if memo:
                    memo_lines = memo.split("\n")
                    # 날짜 박스의 높이에 맞춰 2~3줄까지만 표현
                    display_lines = memo_lines[:2]
                    if len(memo_lines) > 2:
                        display_lines[-1] += "..."
                    
                    # 각 줄마다 아래에서부터 그리기 위해 y 좌표 계산 (역순 순회로 아래에서 위로 쌓기)
                    for i, line in enumerate(reversed(display_lines)):
                        y_offset = y_box + 0.01 + i * 0.0125
                        draw_mixed_text_mpl(ax, x_box + 0.01, y_offset, line, 8, theme_colors['text'], emoji_font_prop,
                                            ha='left', va='bottom')
                    
    # 그림 데이터를 메모리 바이트 스트림으로 변환
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close(fig)
    buf.seek(0)
    return buf

with tab_export:
    st.markdown(f"### 📥 **{cal_name}** 앨범 저장 및 내보내기")
    st.info("이 탭에서는 현재 열심히 꾸민 다이어리 달력을 한 장의 이미지 파일로 저장하거나, 다른 사람들과 공유할 수 있는 수단을 마련해 줍니다.")
    
    export_col1, export_col2 = st.columns([1, 1])
    
    with export_col1:
        st.markdown("#### 🖼️ 달력 이미지 미리보기 & 다운로드")
        st.write("아래 버튼을 누르면 작성한 다이어리를 PNG 이미지로 변환하여 다운로드받을 수 있습니다. 다이어리 소장용이나 SNS 업로드용으로 활용해보세요!")
        
        # 이미지 생성 액션
        generate_image_btn = st.button("🎨 고화질 이미지 생성하기", use_container_width=True)
        
        if generate_image_btn:
            with st.spinner("다이어리를 예쁜 그림으로 변환하고 있어요... 잠시만 기다려주세요! 🧸"):
                try:
                    cal_img_buf = draw_calendar_image(st.session_state.calendar_data, colors)
                    
                    # 다운로드 버튼 활성화
                    st.image(cal_img_buf, caption="생성된 다이어리 이미지 미리보기 (마우스 우클릭 후 다른 이름으로 저장도 가능합니다)", use_container_width=True)
                    
                    # 다운로드 버튼 노출
                    st.download_button(
                        label="📥 달력 PNG 이미지 다운로드",
                        data=cal_img_buf,
                        file_name=f"{cal_name}_diary.png",
                        mime="image/png",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"이미지 생성 중 오류가 발생했습니다: {e}")
                    st.write("상세 디버그 정보:", e)
                    
    with export_col2:
        st.markdown("#### 📁 JSON 백업 데이터 내보내기 / 불러오기")
        st.write("다른 컴퓨터나 환경에서도 다이어리 일정을 계속 이어서 작성하려면 달력 원본 데이터를 백업받으세요.")
        
        # 1. 백업 데이터 다운로드
        json_data = json.dumps(st.session_state.calendar_data, ensure_ascii=False, indent=2)
        st.download_button(
            label="📤 현재 달력 백업 다운로드 (.json)",
            data=json_data,
            file_name=f"{cal_name}_data.json",
            mime="application/json",
            use_container_width=True
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("##### 📥 백업 데이터 복원하기")
        uploaded_file = st.file_uploader("백업받은 .json 파일을 업로드하여 달력을 불러옵니다.", type=["json"])
        
        if uploaded_file is not None:
            try:
                restored_data = json.load(uploaded_file)
                # 데이터 유효성 검사
                if "id" in restored_data and "name" in restored_data and "days" in restored_data:
                    # 새로운 고유 ID 부여하여 충돌 방지 또는 덮어쓰기
                    restore_mode = st.radio("가져오기 방식", ["새 달력으로 추가", "기존 달력에 덮어쓰기"], horizontal=True)
                    
                    restore_confirm = st.button("✅ 데이터 복원 적용", use_container_width=True)
                    if restore_confirm:
                        if restore_mode == "새 달력으로 추가":
                            restored_data["id"] = f"restored_{int(datetime.datetime.now().timestamp())}"
                            restored_data["name"] = f"[복원됨] {restored_data['name']}"
                        
                        save_calendar(restored_data)
                        st.session_state.current_calendar_id = restored_data["id"]
                        save_last_active_id(restored_data["id"])
                        st.success("🎉 데이터가 정상적으로 복원되어 적용되었습니다! 화면을 갱신합니다.")
                        st.rerun()
                else:
                    st.error("올바른 다이어리 백업 파일 양식이 아닙니다.")
            except Exception as e:
                st.error(f"파일을 읽는 도중 오류가 발생했습니다: {e}")
