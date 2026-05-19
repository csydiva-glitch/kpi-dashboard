"""한솔제지 핵심 KPI 실적 및 달성률 대시보드"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import math, io, os
from datetime import date
import firebase_config as fb

# ── 상수 ──────────────────────────────────────────────────────────────────────
TL_GREEN, TL_YELLOW, CAP, WARN_DROP = 90, 70, 200, 20
DIV_ORDER  = ['인쇄', '산업', '감열', '패키징', '친환경', '환경', '혁신']
CAT_ORDER  = ['전략', '혁신', '일반']
TYPE_ORDER = ['KPI', '재무목표']
TL_INFO = {
    'green' : dict(bg='rgba(22,163,74,.08)',   fg='#16A34A', border='rgba(22,163,74,.3)',   label='정상', dot='🟢'),
    'yellow': dict(bg='rgba(234,179,8,.08)',    fg='#EAB308', border='rgba(234,179,8,.3)',   label='주의', dot='🟡'),
    'red'   : dict(bg='rgba(220,38,38,.08)',    fg='#DC2626', border='rgba(220,38,38,.3)',   label='차질', dot='🔴'),
    'gray'  : dict(bg='rgba(156,163,175,.08)', fg='#9CA3AF', border='rgba(156,163,175,.3)', label='N/A',  dot='⚪'),
}

# ── Design tokens (Executive Insight System) ──────────────────────────────────
BG       = '#f7f9fb'   # surface / background
FG       = '#191c1e'   # on-surface
CARD     = '#ffffff'   # surface-container-lowest
BORDER   = '#E2E8F0'   # border-subtle
MUTED    = '#f2f4f6'   # surface-container-low
MUTED_FG = '#43474f'   # on-surface-variant
PRIMARY  = '#001e40'   # primary (dark navy)
PRIMARY_FG = '#ffffff' # on-primary
RADIUS   = '0.5rem'    # xl – cards
RADIUS_SM = '0.25rem'  # lg – buttons/inputs
# Header
HEADER_DARK = '#0F172A'
# Sidebar (light)
SB_BG     = '#ffffff'
SB_BORDER = '#E2E8F0'
SB_FG     = '#191c1e'
SB_MUTED  = '#f2f4f6'
SB_MUTED_FG = '#43474f'
SB_ACTIVE_BG = '#d5e3ff'   # primary-fixed
SB_ACTIVE_FG = '#001b3c'   # on-primary-fixed
SB_ACCENT    = '#0001c0'   # secondary (blue)

st.set_page_config(
    page_title='핵심 KPI 실적 및 달성률',
    page_icon='📊',
    layout='wide',
    initial_sidebar_state='expanded',
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""<link href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600&display=swap" rel="stylesheet">""", unsafe_allow_html=True)
st.markdown(f"""<style>
/* ── Base ──────────────────────────────────────────── */
body, [data-testid="stApp"] {{ font-family:'Inter',sans-serif !important; }}
.kc-val, .kc-sub b, [data-testid="stMetricValue"] {{ font-family:'JetBrains Mono',monospace !important; }}
.sec-hd, .custom-hdr .hdr-title {{ font-family:'Hanken Grotesk',sans-serif !important; }}
[data-testid="stAppViewContainer"], [data-testid="stApp"] {{
  background:{MUTED} !important; color:{FG} !important;
}}
.block-container {{ padding:0 1.5rem 3rem !important; max-width:100% !important; }}
[data-testid="stDecoration"] {{ display:none !important; }}
footer {{ display:none !important; }}
@media(min-width:769px) {{ [data-testid="stHeader"] {{ display:none !important; }} }}
@media(max-width:768px) {{
  [data-testid="stHeader"] {{ background:{HEADER_DARK} !important; border-bottom:1px solid rgba(255,255,255,.1) !important; }}
  [data-testid="stToolbar"] {{ display:none !important; }}
}}

/* ── Sidebar (light) ──────────────────────────────────── */
section[data-testid="stSidebar"] {{
  background:{SB_BG} !important;
  width:240px !important; min-width:240px !important;
  border-right:1px solid {SB_BORDER} !important;
}}
section[data-testid="stSidebar"] > div:first-child {{
  background:{SB_BG} !important; width:240px !important;
  padding-top:0 !important; padding-bottom:160px !important;
}}
[data-testid="stSidebarResizeHandle"] {{ display:none !important; }}
@media(max-width:768px) {{
  section[data-testid="stSidebar"] {{ position:fixed !important; z-index:999 !important; height:100vh !important; }}
}}
section[data-testid="stSidebar"] label {{
  color:{SB_MUTED_FG} !important; font-size:.68rem !important;
  letter-spacing:.04em; font-weight:500 !important;
}}
section[data-testid="stSidebar"] [data-baseweb="select"] > div {{
  background:{SB_BG} !important; border:1px solid {SB_BORDER} !important;
  color:{SB_FG} !important; border-radius:{RADIUS_SM} !important;
}}
section[data-testid="stSidebar"] [data-baseweb="tag"] {{
  background:{SB_ACCENT} !important; color:#fff !important; border-radius:4px !important;
}}
section[data-testid="stSidebar"] [data-testid="stToggle"] span {{ background:{SB_ACCENT} !important; }}

/* Sidebar nav buttons */
section[data-testid="stSidebar"] [data-testid="baseButton-secondary"],
section[data-testid="stSidebar"] [data-testid="baseButton-primary"] {{
  text-align:left !important; font-size:.8rem !important; font-weight:500 !important;
  border-radius:{RADIUS_SM} !important; padding:6px 10px !important; margin-bottom:1px !important;
}}
section[data-testid="stSidebar"] [data-testid="baseButton-secondary"] {{
  background:transparent !important; border:none !important; color:{SB_MUTED_FG} !important;
}}
section[data-testid="stSidebar"] [data-testid="baseButton-secondary"]:hover {{
  background:{SB_MUTED} !important; color:{SB_FG} !important;
}}
section[data-testid="stSidebar"] [data-testid="baseButton-primary"] {{
  background:{SB_ACTIVE_BG} !important; border:none !important; color:{SB_ACTIVE_FG} !important;
}}

/* ── Custom sticky header (dark) ────────────────────── */
.custom-hdr {{
  position:sticky; top:0; z-index:100;
  background:{HEADER_DARK};
  border-bottom:1px solid rgba(255,255,255,.08);
  padding:0 1.5rem; height:64px; margin:0 -1.5rem 1.5rem;
  display:flex; align-items:center; justify-content:space-between;
}}
.hdr-brand {{ display:flex; align-items:center; gap:12px; }}
.hdr-logo {{
  width:36px; height:36px; background:{PRIMARY};
  border-radius:{RADIUS};
  display:flex; align-items:center; justify-content:center; font-size:1rem;
}}
.hdr-title  {{ font-size:.95rem; font-weight:700; color:#ffffff; font-family:'Hanken Grotesk',sans-serif; }}
.hdr-sub    {{ font-size:.67rem; color:rgba(255,255,255,.5); margin-top:1px; }}
.hdr-right  {{ display:flex; align-items:center; gap:10px; }}
.hdr-badge  {{
  background:rgba(255,255,255,.1); color:rgba(255,255,255,.85);
  border:1px solid rgba(255,255,255,.15); border-radius:{RADIUS_SM};
  padding:4px 14px; font-size:.75rem; font-weight:600;
}}
.hdr-date {{ font-size:.68rem; color:rgba(255,255,255,.55); }}

/* ── Section heading ─────────────────────────────────── */
.sec-hd {{
  font-size:.72rem; font-weight:700; color:{MUTED_FG};
  letter-spacing:.08em; text-transform:uppercase;
  font-family:'Inter',sans-serif;
  padding:.5rem 0 .75rem;
  margin:1.25rem 0 .75rem;
  border-bottom:1px solid {BORDER};
}}

/* ── KPI card grid ───────────────────────────────────── */
.kpi-grid {{
  display:grid; grid-template-columns:repeat(4,1fr); gap:1rem; margin-bottom:.75rem;
}}
.kpi-grid-sub {{
  display:grid; grid-template-columns:repeat(3,1fr); gap:1rem; margin-bottom:1.5rem;
}}
@media(max-width:1200px) {{ .kpi-grid {{ grid-template-columns:repeat(2,1fr); }} .kpi-grid-sub {{ grid-template-columns:repeat(2,1fr); }} }}
@media(max-width:640px)  {{ .kpi-grid,.kpi-grid-sub {{ grid-template-columns:1fr; }} }}

.kc {{
  background:{CARD}; border:1px solid {BORDER}; border-radius:{RADIUS};
  padding:1.5rem 1.5rem 1.25rem;
  display:flex; flex-direction:column; justify-content:space-between;
  transition:box-shadow .15s;
}}
.kc:hover {{ box-shadow:0 4px 12px rgba(0,0,0,0.07); }}
/* 색상 구분: 좌측 accent 선 */
.kc-blue   {{ border-left:3px solid #0001c0; }}
.kc-green  {{ border-left:3px solid #16A34A; }}
.kc-red    {{ border-left:3px solid #DC2626; }}
.kc-yellow {{ border-left:3px solid #EAB308; }}
.kc-purple {{ border-left:3px solid #7C3AED; }}
.kc-teal   {{ border-left:3px solid #0891B2; }}
.kc-ico  {{ display:none; }}
.kc-lbl  {{
  font-size:.68rem; color:{MUTED_FG}; font-weight:700;
  letter-spacing:.08em; text-transform:uppercase;
  font-family:'Inter',sans-serif; margin-bottom:.75rem;
}}
.kc-val  {{
  font-size:2.2rem; font-weight:600; line-height:1; margin-bottom:.6rem; color:{FG};
  font-family:'JetBrains Mono',monospace; letter-spacing:-0.01em;
}}
.kc-sub  {{ font-size:.72rem; color:{MUTED_FG}; display:flex; align-items:center; gap:6px; flex-wrap:wrap; }}

/* ── Division card ───────────────────────────────────── */
.dc {{
  background:{CARD}; border:1px solid {BORDER}; border-radius:{RADIUS};
  padding:.8rem;
  box-shadow:0 1px 2px 0 rgba(0,0,0,0.04);
  transition:box-shadow .15s,border-color .15s;
}}
.dc:hover {{ box-shadow:0 4px 8px -2px rgba(0,0,0,0.06); border-color:#9CA3AF; }}
.dc.sel   {{ background:#eef2ff; border-color:{SB_ACCENT}; box-shadow:0 0 0 2px rgba(0,1,192,0.12); }}
.dc .dnm  {{ font-size:.75rem; font-weight:600; color:{FG}; }}
.dc .davg {{ font-size:1.1rem; font-weight:700; }}
.dc .dcnt {{ font-size:.6rem; color:{MUTED_FG}; margin:1px 0 4px; }}
.stk {{ height:4px; border-radius:99px; overflow:hidden; display:flex; margin:4px 0; }}

/* ── Traffic light badge ─────────────────────────────── */
.tl-b {{ display:inline-flex; align-items:center; gap:3px; padding:2px 8px; border-radius:4px; font-size:.68rem; font-weight:500; border:1px solid; }}

/* ── Widget box ──────────────────────────────────────── */
.wb {{ background:{CARD}; border:1px solid {BORDER}; border-radius:{RADIUS}; padding:.9rem 1rem; height:100%;
      box-shadow:0 1px 3px 0 rgba(0,0,0,0.05); }}
.wb h4 {{ font-size:.63rem; font-weight:600; color:{MUTED_FG}; letter-spacing:.07em; text-transform:uppercase; margin:0 0 .6rem; }}

/* ── Top10 item ──────────────────────────────────────── */
.t10 {{ display:flex; gap:6px; padding:5px 0; border-bottom:1px solid {MUTED}; font-size:.73rem; align-items:center; }}
.t10 .rk {{ color:#9CA3AF; font-weight:600; width:16px; flex-shrink:0; }}
.t10 .nm {{ flex:1; color:#43474f; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; }}
.t10 .vl {{ font-weight:700; flex-shrink:0; }}

/* ── Category bar ────────────────────────────────────── */
.cat-row {{ display:flex; gap:8px; align-items:center; padding:5px 0; border-bottom:1px solid {MUTED}; font-size:.73rem; }}
.cat-row .cat-nm {{ width:36px; font-weight:600; color:#43474f; }}
.cat-bar-wrap {{ flex:1; background:{MUTED}; border-radius:99px; height:6px; }}
.cat-bar {{ height:6px; border-radius:99px; }}

/* ── Streamlit widget overrides ──────────────────────── */
[data-baseweb="select"] > div {{
  background:{CARD} !important; border:1px solid {BORDER} !important;
  border-radius:{RADIUS} !important; color:{FG} !important;
}}
[data-baseweb="popover"] li {{ background:{CARD} !important; color:{FG} !important; }}
[data-baseweb="popover"] li:hover {{ background:{MUTED} !important; }}
[data-baseweb="tag"] {{ background:{PRIMARY} !important; color:{PRIMARY_FG} !important; border-radius:4px !important; }}
[data-baseweb="input"] > div {{ background:{CARD} !important; border:1px solid {BORDER} !important; border-radius:{RADIUS} !important; }}
[data-baseweb="input"] input {{ color:{FG} !important; }}
[data-testid="stTextInput"] input {{
  background:{CARD} !important; color:{FG} !important;
  border:1px solid {BORDER} !important; border-radius:{RADIUS} !important;
}}
[data-testid="baseButton-secondary"] {{
  background:{CARD} !important; border:1px solid {BORDER} !important;
  color:#43474f !important; border-radius:{RADIUS} !important; font-weight:500 !important;
  box-shadow:0 1px 2px 0 rgba(0,0,0,0.04) !important;
}}
[data-testid="baseButton-secondary"]:hover {{
  background:{MUTED} !important; border-color:#9CA3AF !important;
}}
[data-testid="baseButton-primary"] {{
  background:{PRIMARY} !important; border:1px solid {PRIMARY} !important;
  color:{PRIMARY_FG} !important; border-radius:{RADIUS} !important; font-weight:500 !important;
}}
[data-testid="stVerticalBlockBorderWrapper"] {{
  background:{CARD} !important; border:1px solid {BORDER} !important;
  border-radius:{RADIUS} !important;
  box-shadow:0 1px 3px 0 rgba(0,0,0,0.05) !important;
}}
[data-testid="stExpander"] {{
  background:{CARD} !important; border:1px solid {BORDER} !important; border-radius:{RADIUS} !important;
}}
[data-testid="stExpanderDetails"] {{ background:{CARD} !important; }}
[data-testid="stTabs"] [role="tablist"] {{ background:transparent !important; border-color:{BORDER} !important; }}
[data-testid="stTabs"] button {{ color:{MUTED_FG} !important; font-weight:500 !important; border-radius:6px 6px 0 0 !important; }}
[data-testid="stTabs"] button[aria-selected="true"] {{ color:{FG} !important; border-bottom-color:{PRIMARY} !important; }}
[data-testid="stCaptionContainer"] p {{ color:{MUTED_FG} !important; }}
[data-testid="stDataEditor"] table {{ background:{CARD} !important; }}
[data-testid="stDataEditor"] th {{
  background:{MUTED} !important; color:#43474f !important;
  border-color:{BORDER} !important; font-weight:600 !important; font-size:.67rem !important;
}}
[data-testid="stDataEditor"] td {{
  background:{CARD} !important; color:{FG} !important; border-color:{MUTED} !important;
}}
[data-testid="metric-container"] {{
  background:{CARD}; border:1px solid {BORDER}; border-radius:{RADIUS}; padding:.5rem .8rem;
  box-shadow:0 1px 2px 0 rgba(0,0,0,0.04);
}}
[data-testid="stMetricLabel"] p {{ color:{MUTED_FG} !important; font-weight:500 !important; font-size:.7rem !important; }}
[data-testid="stMetricValue"] {{ color:{FG} !important; font-weight:700 !important; }}
</style>""", unsafe_allow_html=True)

# ── Business logic ─────────────────────────────────────────────────────────────
def _nan(v): return v is None or (isinstance(v, float) and math.isnan(v))

def calc_ach(plan, actual, xl_ach):
    if _nan(plan) or plan == 0: return None
    a_ok, x_ok = not _nan(actual), not _nan(xl_ach)
    if plan < 0 and a_ok and actual < 0:
        v = abs(plan) / abs(actual) * 100
    elif x_ok: v = float(xl_ach)
    elif a_ok:  v = float(actual) / float(plan) * 100
    else: return None
    return float(max(0, min(CAP, v)))

def get_tl(ach):
    if _nan(ach) or ach is None: return 'gray'
    return 'green' if ach >= TL_GREEN else ('yellow' if ach >= TL_YELLOW else 'red')

def fmt_ach(ach): return f"{ach:.1f}%" if ach is not None else "N/A"

def stk_html(cnt, total):
    c = dict(green='#16A34A', yellow='#EAB308', red='#DC2626', gray='#D1D5DB')
    if not total: return f'<div class="stk"><div style="flex:1;background:{BORDER}"></div></div>'
    segs = ''.join(f'<div style="flex:{cnt.get(k,0)};background:{c[k]}"></div>'
                   for k in ['green','yellow','red'] if cnt.get(k,0)>0)
    return f'<div class="stk">{segs}</div>'

def trend_html(delta):
    if delta is None: return ''
    sign, clr = ('▲','#16A34A') if delta > 0 else ('▼','#DC2626')
    return f'<span style="color:{clr};font-weight:600;font-size:.7rem">{sign}{abs(delta):.1f}%p 전월비</span>'

# ── Data loading ───────────────────────────────────────────────────────────────
@st.cache_data(show_spinner='데이터 처리 중...')
def load_data(raw: bytes) -> pd.DataFrame:
    try:    tables = pd.read_html(io.BytesIO(raw), encoding='utf-8')
    except: tables = pd.read_html(io.BytesIO(raw))
    raw_df = (tables[1] if len(tables)>1 else tables[0]).copy()
    return raw_df  # load_data_raw가 나중에 정의되므로 여기선 raw 반환 후 재처리

# ── Session state ──────────────────────────────────────────────────────────────
_defaults = [
    ('memos', {}), ('sel_div', None), ('sel_fin_div', None),
    ('page', 'home'), ('ki_sel_div', DIV_ORDER[0]),
    ('logged_in', False), ('id_token', None),
    ('user_email', ''), ('user_name', ''),
]
for k, v in _defaults:
    if k not in st.session_state: st.session_state[k] = v

# ── Firebase 로그인 페이지 ───────────────────────────────────────────────────
_fb_ready = fb.is_firebase_available()

if _fb_ready and not st.session_state.logged_in:
    st.markdown(f"""<style>
    [data-testid="stForm"] {{ border:none !important; padding:0 !important; }}
    </style>""", unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:1.5rem">
          <div style="background:{PRIMARY};border-radius:{RADIUS};width:36px;height:36px;
                      display:flex;align-items:center;justify-content:center;font-size:1rem">📊</div>
          <div>
            <div style="font-size:.95rem;font-weight:600;color:{FG}">핵심 KPI 대시보드</div>
            <div style="font-size:.67rem;color:{MUTED_FG}">로그인하여 계속하세요</div>
          </div>
        </div>""", unsafe_allow_html=True)

        with st.form('login_form'):
            email    = st.text_input('이메일', placeholder='user@hansol.com')
            password = st.text_input('비밀번호', type='password')
            submitted = st.form_submit_button('로그인', use_container_width=True, type='primary')

        if submitted:
            if not email or not password:
                st.error('이메일과 비밀번호를 입력하세요.')
            else:
                with st.spinner('로그인 중...'):
                    result = fb.sign_in(email, password)
                if result['ok']:
                    st.session_state.logged_in   = True
                    st.session_state.id_token    = result['id_token']
                    st.session_state.user_email  = result['email']
                    st.session_state.user_name   = result['display_name']
                    st.rerun()
                else:
                    st.error(result['error'])
    st.stop()

# ══════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════
_user_line = (f'<div style="font-size:.6rem;color:{SB_MUTED_FG};margin-top:4px;'
              f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'
              f'🔒 {st.session_state.user_email}</div>'
              if st.session_state.logged_in else '')
st.sidebar.markdown(f"""
<div style="background:{SB_BG};padding:1.4rem 1rem 1rem;
            border-bottom:1px solid {SB_BORDER};margin:-1rem -1rem .75rem">
  <div style="font-size:1rem;font-weight:700;color:{PRIMARY};
              font-family:'Hanken Grotesk',sans-serif;line-height:1.2;margin-bottom:2px">
    Hansol Paper
  </div>
  <div style="font-size:.72rem;color:{SB_MUTED_FG};margin-bottom:6px">
    Executive KPI Dashboard
  </div>
  {_user_line}
</div>""", unsafe_allow_html=True)

if st.session_state.logged_in:
    if st.sidebar.button('🔓  로그아웃', key='logout', use_container_width=True):
        for k in ('logged_in', 'id_token', 'user_email', 'user_name'):
            st.session_state[k] = False if k == 'logged_in' else (None if k == 'id_token' else '')
        st.rerun()

# 보고 월
st.sidebar.markdown(f'<p style="font-size:.65rem;color:{SB_MUTED_FG};font-weight:500;letter-spacing:.04em;margin:.5rem 0 .2rem">📅 보고 월</p>', unsafe_allow_html=True)
m_opts = ['미선택'] + [f'{m}월' for m in range(1,13)]
m_sel  = st.sidebar.selectbox('보고 월', m_opts, index=0, key='f_month', label_visibility='collapsed')
month  = None if m_sel == '미선택' else int(m_sel[:-1])

# Navigation
st.sidebar.markdown(f'<div style="margin:.9rem 0 .3rem;font-size:.6rem;color:{SB_MUTED_FG};font-weight:600;letter-spacing:.08em;text-transform:uppercase">Navigation</div>', unsafe_allow_html=True)
_cur_page = st.session_state.get('page', 'home')
for _icon, _label, _key in [
    ('📊', '전사 요약',    'home'),
    ('🏢', '부문·KI 상세', 'ki_detail'),
]:
    if st.sidebar.button(f'{_icon}  {_label}', key=f'nav_{_key}',
                         use_container_width=True,
                         type='primary' if _cur_page == _key else 'secondary'):
        st.session_state.page = _key
        st.rerun()

st.sidebar.markdown(f'<hr style="border:none;border-top:1px solid {SB_BORDER};margin:.6rem 0"><div style="font-size:.6rem;color:{SB_MUTED_FG};font-weight:600;letter-spacing:.08em;text-transform:uppercase;margin-bottom:.4rem">Filters</div>', unsafe_allow_html=True)

sel_div  = st.sidebar.selectbox('🏢 부문',    ['전체'] + DIV_ORDER,  key='f_div')
sel_cat  = st.sidebar.selectbox('📁 분류',    ['전체'] + CAT_ORDER,  key='f_cat')
sel_type = st.sidebar.selectbox('📌 지표구분', ['전체'] + TYPE_ORDER, key='f_type')
st.sidebar.markdown('<div style="height:4px"></div>', unsafe_allow_html=True)
key_only = st.sidebar.toggle('⭐ 핵심 KPI만', value=False, key='f_key')

# ══════════════════════════════════════════════════════
# MAIN AREA — Header
# ══════════════════════════════════════════════════════
month_badge = f'{month}월' if month else '월 미선택'
_user_badge = (f'<div class="hdr-date" style="display:flex;align-items:center;gap:5px">'
               f'<span style="font-size:.75rem">👤</span>'
               f'<span>{st.session_state.user_name or st.session_state.user_email}</span></div>'
               if st.session_state.logged_in else '')
_src_badge  = (f'<div style="font-size:.65rem;color:{MUTED_FG};background:{MUTED};'
               f'border:1px solid {BORDER};border-radius:4px;padding:2px 8px">🔥 Firestore</div>'
               if (st.session_state.logged_in and fb.is_firebase_available()) else '')
st.markdown(f"""
<div class="custom-hdr">
  <div class="hdr-brand">
    <div class="hdr-logo">📊</div>
    <div>
      <div class="hdr-title">Hansol Paper Executive Dashboard</div>
      <div class="hdr-sub">핵심 KPI 실적 및 달성률</div>
    </div>
  </div>
  <div class="hdr-right">
    {_src_badge}
    <div class="hdr-badge">{month_badge}</div>
    {_user_badge}
    <div class="hdr-date">as of {date.today():%Y-%m-%d}</div>
  </div>
</div>""", unsafe_allow_html=True)

# ── Data loading (Firestore 우선 → 로컬 XLS fallback) ─────────────────────────
@st.cache_data(ttl=300, show_spinner='Firestore에서 데이터 로드 중...')
def load_data_firestore() -> pd.DataFrame | None:
    records = fb.load_kpi_records()
    if not records:
        return None
    return load_data_raw(pd.DataFrame(records))

def load_data_raw(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    if '삭제여부' in df.columns: df.drop(columns=['삭제여부'], inplace=True)
    if '분류' in df.columns:
        df['분류'] = df['분류'].astype(str).str.replace('/', '', regex=False).str.strip()
    for c in ['연간 계획','당월 누계 계획','당월 누계 실적','달성율(%)','진척율(%)']:
        if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce')
    for old, new in [('KPI/재무목표','지표명'),('지표','구분'),('핵심KPI','차별화')]:
        if old in df.columns: df.rename(columns={old:new}, inplace=True)
    if '세부실행과제' in df.columns: df['세부실행과제'] = df['세부실행과제'].fillna('')
    if '월' in df.columns: df['월'] = pd.to_numeric(df['월'], errors='coerce')
    df['KPI_ID'] = (df.get('부문',pd.Series(dtype=str)).fillna('').astype(str)+'|'+
                    df.get('KI',  pd.Series(dtype=str)).fillna('').astype(str).str[:50]+'|'+
                    df.get('지표명',pd.Series(dtype=str)).fillna('').astype(str))
    df['_ach'] = df.apply(lambda r: calc_ach(
        r.get('당월 누계 계획'), r.get('당월 누계 실적'), r.get('달성율(%)')), axis=1)
    df['_tl'] = df['_ach'].apply(get_tl)
    prev_map = {}
    for kid, sub in df.groupby('KPI_ID'):
        m2a = {int(m): a for m,a in zip(sub['월'], sub['_ach']) if not _nan(m)}
        for m in range(2,13):
            if m in m2a: prev_map[(kid,m)] = m2a.get(m-1)
    def d_fn(r):
        m = r.get('월')
        if _nan(m) or int(m)<=1: return None
        prev = prev_map.get((r['KPI_ID'], int(m)))
        cur  = r['_ach']
        return (cur-prev) if (prev is not None and cur is not None) else None
    df['_delta'] = df.apply(d_fn, axis=1)
    df['_warn']  = df['_delta'].apply(lambda d: d is not None and d<=-WARN_DROP)
    return df

df = None
_use_firestore = _fb_ready and st.session_state.logged_in
LOCAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), '25년 실적.xls')

if _use_firestore:
    df = load_data_firestore()

if df is None:
    if os.path.exists(LOCAL):
        with open(LOCAL,'rb') as fh: df = load_data_raw(load_data(fh.read()))
    else:
        up = st.file_uploader('📂 25년 실적.xls 업로드', type=['xls','xlsx','html'],
                              label_visibility='collapsed')
        if up: df = load_data_raw(load_data(up.getvalue()))

if df is None:
    st.markdown(f"""
    <div style="text-align:center;padding:100px 0;color:{MUTED_FG}">
      <div style="font-size:2.5rem">📊</div>
      <div style="font-size:.95rem;font-weight:500;margin-top:12px;color:{MUTED_FG}">
        {'Firestore에 데이터가 없습니다. 아래 데이터 요약 섹션에서 XLS를 업로드하세요.' if _use_firestore
         else '사이드바에서 파일을 업로드하거나 같은 폴더에 25년 실적.xls를 넣어주세요'}
      </div>
    </div>""", unsafe_allow_html=True)
    st.stop()

if month is None:
    st.markdown(f"""
    <div style="text-align:center;padding:100px 0;color:{MUTED_FG}">
      <div style="font-size:2.5rem">📅</div>
      <div style="font-size:.95rem;font-weight:500;margin-top:12px;color:{MUTED_FG}">
        좌측 사이드바에서 보고 월을 선택하세요
      </div>
    </div>""", unsafe_allow_html=True)
    st.stop()

# ── Filter ─────────────────────────────────────────────────────────────────────
mdf = df[df['월'] == month].copy()

def apply_filter(d):
    mask = pd.Series(True, index=d.index)
    if '부문' in d.columns and sel_div  != '전체': mask &= d['부문'] == sel_div
    if '분류' in d.columns and sel_cat  != '전체': mask &= d['분류'] == sel_cat
    if '구분' in d.columns and sel_type != '전체': mask &= d['구분'] == sel_type
    if key_only and '차별화' in d.columns:
        mask &= d['차별화'].astype(str).str.strip().str.upper() == 'Y'
    return d[mask]

fdf_all = apply_filter(mdf)               # gray 포함 전체 (재무목표 계산용)
fdf = fdf_all[fdf_all['_tl'] != 'gray']  # 미산출 제외 (KPI 통계용)

if month > 1:
    prev_fdf = apply_filter(df[df['월']==month-1].copy())
    prev_fdf = prev_fdf[prev_fdf['_tl'] != 'gray']
    prev_avg = prev_fdf['_ach'].dropna().mean() if len(prev_fdf) else None
else:
    prev_avg = None

tot  = len(fdf)
achs = fdf['_ach'].dropna()
avg  = achs.mean() if len(achs) else None
cnt  = {k: int((fdf['_tl']==k).sum()) for k in TL_INFO}
key_cnt  = int((fdf['차별화'].astype(str).str.upper()=='Y').sum()) if '차별화' in fdf.columns else 0
warn_cnt = int(fdf['_warn'].sum())

fin_mask = (fdf_all['구분']=='재무목표') if '구분' in fdf_all.columns else pd.Series(False, index=fdf_all.index)
_fin_s   = fdf_all.loc[fin_mask,'_ach'].dropna() if fin_mask.any() else pd.Series(dtype=float)
fin_avg  = _fin_s.mean() if len(_fin_s) else None
_key_s   = fdf.loc[fdf['차별화'].astype(str).str.upper()=='Y','_ach'].dropna() \
           if '차별화' in fdf.columns else pd.Series(dtype=float)
key_avg  = _key_s.mean() if len(_key_s) else None
avg_delta = (avg - prev_avg) if (avg is not None and prev_avg is not None) else None

# ── 신호등 범례 — 사이드바 하단 고정 ─────────────────────────────────────────
_tl_thresholds = {'green': f'≥{TL_GREEN}%', 'yellow': f'{TL_YELLOW}~{TL_GREEN}%', 'red': f'<{TL_YELLOW}%', 'gray': '미산출'}
_legend_rows = ''.join(f"""
  <div style="display:flex;align-items:center;justify-content:space-between;padding:3px 0">
    <div style="display:flex;align-items:center;gap:7px">
      <div style="width:8px;height:8px;border-radius:50%;background:{TL_INFO[k]['fg']};flex-shrink:0"></div>
      <div>
        <span style="font-size:.72rem;color:{TL_INFO[k]['fg']};font-weight:600">{TL_INFO[k]['label']}</span>
        <span style="font-size:.6rem;color:{SB_MUTED_FG};margin-left:4px">{_tl_thresholds[k]}</span>
      </div>
    </div>
    <span style="font-size:.72rem;color:{TL_INFO[k]['fg']};font-weight:700">{cnt.get(k,0)}<span style="font-size:.6rem;color:{SB_MUTED_FG};font-weight:400">건</span></span>
  </div>""" for k in ['green','yellow','red'])

st.sidebar.markdown(f"""
<div style="position:fixed;bottom:0;left:0;width:240px;
            padding:.8rem 1rem .9rem;border-top:1px solid {SB_BORDER};
            background:{SB_BG};box-sizing:border-box;z-index:200">
  <div style="font-size:.6rem;color:{SB_MUTED_FG};font-weight:600;letter-spacing:.08em;
              text-transform:uppercase;margin-bottom:.45rem">신호등 범례</div>
  {_legend_rows}
  <div style="font-size:.58rem;color:{SB_MUTED_FG};margin-top:.55rem;padding-top:.45rem;border-top:1px solid {SB_BORDER}">
    Data as of {date.today():%Y-%m-%d} · {month}월 기준
  </div>
</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# PAGE: 부문·KI 상세
# ══════════════════════════════════════════════════════
if st.session_state.get('page', 'home') == 'ki_detail':
    st.markdown('<div class="sec-hd">부문·KI 상세</div>', unsafe_allow_html=True)

    avail_divs = [d for d in DIV_ORDER if '부문' in fdf.columns and d in fdf['부문'].values]
    if not avail_divs:
        st.info('필터 조건에 맞는 데이터가 없습니다.')
        st.stop()

    ki_col = 'KI' if 'KI' in fdf.columns else None

    tabs = st.tabs(avail_divs)
    for tab, div in zip(tabs, avail_divs):
        with tab:
            div_df = fdf[fdf['부문'] == div].copy()
            ki_list = ([k for k in div_df[ki_col].dropna().unique() if str(k).strip() and str(k) != 'nan']
                       if ki_col else [])

            if not ki_list:
                st.caption('KI 데이터가 없습니다.')
            else:
                N = 4
                for i in range(0, len(ki_list), N):
                    chunk = ki_list[i:i+N]
                    cols  = st.columns(len(chunk))
                    for col, ki in zip(cols, chunk):
                        ki_rows = div_df[div_df[ki_col] == ki]
                        kt  = len(ki_rows)
                        ka  = ki_rows['_ach'].dropna().mean() if kt else None
                        ktl = get_tl(ka)
                        kcc = {k: int((ki_rows['_tl']==k).sum()) for k in TL_INFO}
                        kk  = int((ki_rows['차별화'].astype(str).str.upper()=='Y').sum()) \
                              if '차별화' in ki_rows.columns else 0
                        with col:
                            st.markdown(f"""
<div class="dc">
  <div class="dnm" style="font-size:.7rem;line-height:1.3;margin-bottom:4px">{ki}</div>
  <div class="davg" style="color:{TL_INFO[ktl]['fg']}">{f'{ka:.0f}%' if ka is not None else 'N/A'}</div>
  <div class="dcnt">KPI {kt}건 · ⭐{kk}</div>
  {stk_html(kcc, kt)}
  <div style="font-size:.6rem;color:{MUTED_FG};display:flex;gap:5px;margin-top:2px">
    <span>🟢{kcc['green']}</span><span>🟡{kcc['yellow']}</span>
    <span>🔴{kcc['red']}</span>
  </div>
</div>""", unsafe_allow_html=True)

                st.markdown('<div style="height:.6rem"></div>', unsafe_allow_html=True)

                for ki in ki_list:
                    ki_rows = div_df[div_df[ki_col] == ki].copy()
                    kt  = len(ki_rows)
                    ka  = ki_rows['_ach'].dropna().mean() if kt else None
                    ktl = get_tl(ka)
                    ach_str = f'{ka:.1f}%' if ka is not None else 'N/A'
                    exp_label = f"{TL_INFO[ktl]['dot']}  {ki}  ({ach_str} / {kt}건)"
                    with st.expander(exp_label, expanded=False):
                        tbl_data = []
                        for _, r in ki_rows.sort_values('_ach', ascending=True, na_position='last').iterrows():
                            ach   = r['_ach']
                            tl    = r['_tl']
                            delta = r['_delta']
                            is_key = str(r.get('차별화','')).strip().upper() == 'Y'
                            d_str = ''
                            if delta is not None:
                                d_str = f"{'▲' if delta>0 else '▼'}{abs(delta):.1f}%p"
                            tbl_data.append({
                                '⭐':      '⭐' if is_key else '',
                                '분류':    str(r.get('분류','')),
                                '구분':    str(r.get('구분','')),
                                '지표명':  str(r.get('지표명','')),
                                '단위':    str(r.get('단위','')),
                                '누계계획': r.get('당월 누계 계획'),
                                '누계실적': r.get('당월 누계 실적'),
                                '달성률':  ach,
                                '신호등':  TL_INFO[tl]['dot']+' '+TL_INFO[tl]['label'],
                                '전월대비': d_str,
                                '⚠':       '⚠ 급락' if r['_warn'] else '',
                            })
                        if tbl_data:
                            ki_tdf = pd.DataFrame(tbl_data)
                            ki_cfg = {
                                '⭐':       st.column_config.TextColumn('⭐', disabled=True, width='small'),
                                '누계계획': st.column_config.NumberColumn('누계계획', format='%.2f'),
                                '누계실적': st.column_config.NumberColumn('누계실적', format='%.2f'),
                                '달성률':   st.column_config.NumberColumn('달성률(%)', format='%.1f'),
                            }
                            for c in ki_tdf.columns:
                                if c not in ki_cfg:
                                    ki_cfg[c] = st.column_config.TextColumn(c, disabled=True)
                            st.dataframe(ki_tdf, column_config=ki_cfg,
                                         hide_index=True, use_container_width=True)

    st.stop()

# ══════════════════════════════════════════════════════
# ① KPI SUMMARY CARDS
# ══════════════════════════════════════════════════════
st.markdown('<div id="sec-summary"></div>', unsafe_allow_html=True)
st.markdown('<div class="sec-hd">전사 핵심 KPI 요약</div>', unsafe_allow_html=True)

def kc_trend(delta):
    if delta is None: return ''
    s,c = ('▲','#16A34A') if delta>0 else ('▼','#DC2626')
    return f'<span style="color:{c};font-weight:600">{s}{abs(delta):.1f}%p</span> 전월비'

def avg_color(a):
    if a is None: return '#6B7280'
    return '#16A34A' if a>=TL_GREEN else ('#D97706' if a>=TL_YELLOW else '#DC2626')

st.markdown(f"""
<div class="kpi-grid">
  <div class="kc kc-blue">
    <div class="kc-lbl">전사 평균 달성률</div>
    <div class="kc-val" style="color:{avg_color(avg)}">{fmt_ach(avg)}</div>
    <div class="kc-sub">KPI {tot}건 전체 · {kc_trend(avg_delta)}</div>
  </div>
  <div class="kc kc-green">
    <div class="kc-lbl">정상 달성</div>
    <div class="kc-val" style="color:#16A34A">{cnt['green']}<span style="font-size:1rem;font-weight:400;color:#9CA3AF">건</span></div>
    <div class="kc-sub">{cnt['green']/tot*100 if tot else 0:.0f}% of {tot}건</div>
  </div>
  <div class="kc kc-yellow">
    <div class="kc-lbl">주의 KPI</div>
    <div class="kc-val" style="color:#EAB308">{cnt['yellow']}<span style="font-size:1rem;font-weight:400;color:#9CA3AF">건</span></div>
    <div class="kc-sub">{cnt['yellow']/tot*100 if tot else 0:.0f}% of {tot}건</div>
  </div>
  <div class="kc kc-red">
    <div class="kc-lbl">차질 KPI</div>
    <div class="kc-val" style="color:#DC2626">{cnt['red']}<span style="font-size:1rem;font-weight:400;color:#9CA3AF">건</span></div>
    <div class="kc-sub">{cnt['red']/tot*100 if tot else 0:.0f}% of {tot}건 · 즉시 점검</div>
  </div>
</div>
<div class="kpi-grid-sub">
  <div class="kc kc-purple">
    <div class="kc-lbl">핵심 KPI 달성률</div>
    <div class="kc-val" style="color:{avg_color(key_avg)}">{fmt_ach(key_avg)}</div>
    <div class="kc-sub">핵심 {key_cnt}건 기준</div>
  </div>
  <div class="kc kc-teal">
    <div class="kc-lbl">재무목표 달성률</div>
    <div class="kc-val" style="color:{avg_color(fin_avg)}">{fmt_ach(fin_avg)}</div>
    <div class="kc-sub">재무목표 {int(fin_mask.sum())}건 기준</div>
  </div>
  <div class="kc kc-yellow">
    <div class="kc-lbl">전월 대비 급락</div>
    <div class="kc-val" style="color:#EAB308">{warn_cnt}<span style="font-size:1rem;font-weight:400;color:#9CA3AF">건</span></div>
    <div class="kc-sub">−{WARN_DROP}%p 이상 하락 경보</div>
  </div>
</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# ② DIVISION CARDS
# ══════════════════════════════════════════════════════
st.markdown('<div id="sec-div"></div>', unsafe_allow_html=True)
st.markdown('<div class="sec-hd">부문별 현황</div>', unsafe_allow_html=True)

_div_rows_html = ''
for _div in DIV_ORDER:
    _dr  = fdf[fdf['부문']==_div] if '부문' in fdf.columns else pd.DataFrame()
    _dt  = len(_dr)
    _dc  = {k: int((_dr['_tl']==k).sum()) for k in TL_INFO}
    _da  = _dr['_ach'].dropna().mean() if _dt else None
    _dtl = get_tl(_da)
    _dk  = int((_dr['차별화'].astype(str).str.upper()=='Y').sum()) if '차별화' in _dr.columns else 0
    _clr = TL_INFO[_dtl]['fg']
    _ach_str = f"{_da:.1f}%" if _da is not None else "N/A"
    _bar = stk_html(_dc, _dt).replace('\n','')
    _div_rows_html += f"""
      <tr style="border-bottom:1px solid {BORDER}">
        <td style="padding:.7rem 1rem;font-weight:600;color:{FG};font-size:.82rem">{_div}</td>
        <td style="padding:.7rem 1rem;color:{_clr};font-family:'JetBrains Mono',monospace;font-weight:700;font-size:.9rem">{_ach_str}</td>
        <td style="padding:.7rem 1rem;text-align:center;color:#16A34A;font-weight:700;font-size:.82rem">{_dc['green']}</td>
        <td style="padding:.7rem 1rem;text-align:center;color:#EAB308;font-weight:700;font-size:.82rem">{_dc['yellow']}</td>
        <td style="padding:.7rem 1rem;text-align:center;color:#DC2626;font-weight:700;font-size:.82rem">{_dc['red']}</td>
        <td style="padding:.7rem 1rem;text-align:center;color:{MUTED_FG};font-size:.82rem">{_dt}</td>
        <td style="padding:.7rem 1rem;text-align:center;color:{MUTED_FG};font-size:.82rem">{_dk}</td>
        <td style="padding:.7rem 1rem;min-width:80px">{_bar}</td>
      </tr>"""

_th  = f"padding:.55rem 1rem;text-align:left;font-size:.63rem;font-weight:700;color:{MUTED_FG};letter-spacing:.07em;text-transform:uppercase;white-space:nowrap"
_thc = _th.replace("text-align:left","text-align:center")
st.markdown(f"""
<div style="background:{CARD};border:1px solid {BORDER};border-radius:{RADIUS};overflow:hidden;margin-bottom:1.5rem">
  <table style="width:100%;border-collapse:collapse">
    <thead>
      <tr style="background:{MUTED};border-bottom:2px solid {BORDER}">
        <th style="{_th}">부문</th>
        <th style="{_th}">평균 달성률</th>
        <th style="{_thc}">🟢 정상</th>
        <th style="{_thc}">🟡 주의</th>
        <th style="{_thc}">🔴 차질</th>
        <th style="{_thc}">전체</th>
        <th style="{_thc}">⭐ 핵심</th>
        <th style="{_thc}">현황</th>
      </tr>
    </thead>
    <tbody>{_div_rows_html}
    </tbody>
  </table>
</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# ③ DETAIL TABLE
# ══════════════════════════════════════════════════════
st.markdown('<div id="sec-detail"></div>', unsafe_allow_html=True)
hd_txt = 'KPI 상세' + (' — ⭐ 핵심 KPI' if key_only else '')
st.markdown(f'<div class="sec-hd">{hd_txt}</div>', unsafe_allow_html=True)

det = fdf.copy()

dk2 = int((det['차별화'].astype(str).str.upper()=='Y').sum()) if '차별화' in det.columns else 0
_div_label = f"📌 {sel_div} · " if sel_div != '전체' else ''
st.caption(f"{_div_label}전체 {len(det)}건 · ⭐ 핵심 {dk2}건 · 일반 {len(det)-dk2}건")

sc1, sc2 = st.columns([4,1])
with sc1:
    srch = st.text_input('🔍', placeholder='지표명 검색...', label_visibility='collapsed', key='srch')
with sc2:
    sort_opt = st.selectbox('정렬', ['달성률 ↑','달성률 ↓','부문','지표명'],
                            label_visibility='collapsed', key='sort_opt')

if srch and '지표명' in det.columns:
    det = det[det['지표명'].str.contains(srch, case=False, na=False)]
if sort_opt=='달성률 ↑':   det = det.sort_values('_ach', ascending=True,  na_position='last')
elif sort_opt=='달성률 ↓': det = det.sort_values('_ach', ascending=False, na_position='last')
elif sort_opt=='부문'   and '부문'   in det.columns: det=det.sort_values('부문')
elif sort_opt=='지표명' and '지표명' in det.columns: det=det.sort_values('지표명')

tbl_rows, kid_list = [], []
for _, r in det.iterrows():
    kid   = r.get('KPI_ID','')
    ach   = r['_ach']
    tl    = r['_tl']
    delta = r['_delta']
    warn  = r['_warn']
    is_key = str(r.get('차별화','')).strip().upper() == 'Y'
    d_str = ''
    if delta is not None:
        d_str = f"{'▲' if delta>0 else '▼'}{abs(delta):.1f}%p"
    tbl_rows.append({
        '⭐':      '⭐' if is_key else '',
        '부문':    str(r.get('부문','')),
        'KI':      str(r.get('KI','')),
        '분류':    str(r.get('분류','')),
        '구분':    str(r.get('구분','')),
        '지표명':  str(r.get('지표명','')),
        '단위':    str(r.get('단위','')),
        '누계계획': r.get('당월 누계 계획'),
        '누계실적': r.get('당월 누계 실적'),
        '달성률':  ach,
        '신호등':  TL_INFO[tl]['dot']+' '+TL_INFO[tl]['label'],
        '전월대비': d_str,
        '⚠':       '⚠ 급락' if warn else '',
        '메모':    st.session_state.memos.get(kid,''),
    })
    kid_list.append(kid)

tbl_df = pd.DataFrame(tbl_rows).reset_index(drop=True)
disp_cols = ['⭐','부문','KI','분류','구분','지표명','단위','누계계획','누계실적','달성률','신호등','전월대비','⚠','메모']
col_cfg = {
    '⭐':       st.column_config.TextColumn('⭐', disabled=True, width='small'),
    '누계계획': st.column_config.NumberColumn('누계계획', format='%.2f'),
    '누계실적': st.column_config.NumberColumn('누계실적', format='%.2f'),
    '달성률':   st.column_config.NumberColumn('달성률(%)', format='%.1f'),
    '메모':     st.column_config.TextColumn('메모', disabled=False, width='medium'),
}
for c in disp_cols:
    if c not in col_cfg: col_cfg[c] = st.column_config.TextColumn(c, disabled=True)

edited = st.data_editor(tbl_df[disp_cols], column_config=col_cfg, hide_index=True,
                        use_container_width=True, num_rows='fixed', height=420, key='det_ed')
if edited is not None and '메모' in edited.columns:
    for i, mv in enumerate(edited['메모'].tolist()):
        if i < len(kid_list) and kid_list[i]:
            if mv: st.session_state.memos[kid_list[i]] = str(mv)
            elif kid_list[i] in st.session_state.memos: del st.session_state.memos[kid_list[i]]

# ══════════════════════════════════════════════════════
# ④ FINANCIAL SECTION
# ══════════════════════════════════════════════════════
st.markdown('<div id="sec-fin"></div>', unsafe_allow_html=True)
st.markdown('<div class="sec-hd">재무목표</div>', unsafe_allow_html=True)

fin_base = mdf.copy()
if '부문' in fin_base.columns and sel_div  != '전체': fin_base = fin_base[fin_base['부문'] == sel_div]
if '분류' in fin_base.columns and sel_cat  != '전체': fin_base = fin_base[fin_base['분류'] == sel_cat]
fin_df = fin_base[fin_base['구분']=='재무목표'].copy() if '구분' in fin_base.columns else pd.DataFrame()

if fin_df.empty:
    st.caption('재무목표 데이터가 없습니다.')
else:
    fin_divs = [d for d in DIV_ORDER if '부문' in fin_df.columns and d in fin_df['부문'].values]
    if fin_divs:
        if st.session_state.sel_fin_div:
            if st.button(f'← 재무목표 전체  (현재: {st.session_state.sel_fin_div})', key='rst_fin'):
                st.session_state.sel_fin_div = None
                st.rerun()
        fdcols = st.columns(min(len(fin_divs),7))
        for col, div in zip(fdcols, fin_divs):
            dr  = fin_df[fin_df['부문']==div]
            da  = dr['_ach'].dropna().mean() if len(dr) else 0.0
            dtl = get_tl(da if len(dr) else None)
            dc  = {k: int((dr['_tl']==k).sum()) for k in TL_INFO}
            is_sel = st.session_state.sel_fin_div == div
            with col:
                st.markdown(f"""
                <div class="dc {'sel' if is_sel else ''}">
                  <div class="dnm">{div}</div>
                  <div class="davg" style="color:{TL_INFO[dtl]['fg']}">{da:.0f}%</div>
                  <div class="dcnt">{len(dr)}건</div>
                  {stk_html(dc, len(dr))}
                </div>""", unsafe_allow_html=True)
                if st.button('✓' if is_sel else '▶', key=f'fb_{div}',
                             use_container_width=True, type='primary' if is_sel else 'secondary'):
                    st.session_state.sel_fin_div = None if is_sel else div
                    st.rerun()

    if st.session_state.sel_fin_div and '지표명' in fin_df.columns:
        sel_rows = fin_df[fin_df['부문']==st.session_state.sel_fin_div]
        st.dataframe(
            sel_rows[['KI','지표명','단위','당월 누계 계획','당월 누계 실적']].assign(
                달성률=sel_rows['_ach'].round(1),
                신호등=sel_rows['_tl'].map(lambda t: TL_INFO[t]['dot']+' '+TL_INFO[t]['label'])
            ).rename(columns={'당월 누계 계획':'누계계획','당월 누계 실적':'누계실적'}),
            hide_index=True, use_container_width=True,
        )
        kpi_opts = sel_rows['지표명'].unique().tolist()
        sel_kpi  = st.selectbox('지표 선택', kpi_opts, key='fin_kpi')
        tab_c, tab_m = st.tabs(['📈 누계', '📊 단월'])
        ks = df[(df['부문']==st.session_state.sel_fin_div)&(df['지표명']==sel_kpi)].sort_values('월')
        months  = ks['월'].tolist()
        c_plan  = ks['당월 누계 계획'].tolist()
        c_act   = ks['당월 누계 실적'].tolist()
        m_plan  = [c_plan[0] if c_plan else None]+[(c_plan[i]-c_plan[i-1]) if not(_nan(c_plan[i]) or _nan(c_plan[i-1])) else None for i in range(1,len(c_plan))]
        m_act   = [c_act[0]  if c_act  else None]+[(c_act[i] -c_act[i-1])  if not(_nan(c_act[i])  or _nan(c_act[i-1]))  else None for i in range(1,len(c_act))]
        m_ach   = [calc_ach(p,a,None) for p,a in zip(m_plan,m_act)]
        CHART_LAYOUT = dict(
            paper_bgcolor='#FFFFFF', plot_bgcolor='#FAFAFA',
            font=dict(color='#444444', size=11), margin=dict(t=20,b=20,l=0,r=0),
            xaxis=dict(tickvals=list(range(1,13)), ticktext=[f'{m}월' for m in range(1,13)],
                       gridcolor='#F0F0F0', linecolor='#E5E5E5', zerolinecolor='#E5E5E5'),
            yaxis=dict(gridcolor='#F0F0F0', linecolor='#E5E5E5', zerolinecolor='#E5E5E5'),
            legend=dict(orientation='h', yanchor='bottom', y=1.02),
        )
        with tab_c:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=months,y=c_plan,mode='lines',name='계획',
                                     line=dict(color='#D1D5DB',dash='dash',width=2)))
            fig.add_trace(go.Scatter(x=months,y=c_act,mode='lines+markers',name='실적',
                                     line=dict(color='#EAB308',width=2),
                                     marker=dict(size=6,color='#3B6EDE',line=dict(color='white',width=1.5))))
            fig.update_layout(height=280, **CHART_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)
        with tab_m:
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(x=months,y=m_plan,name='계획',marker_color='#E5E7EB'))
            fig2.add_trace(go.Bar(x=months,y=m_act, name='실적',marker_color='#3B6EDE'))
            fig2.add_trace(go.Scatter(x=months,y=m_ach,name='달성률(%)',mode='lines+markers',
                                      line=dict(color='#D97706',width=2),
                                      marker=dict(size=5,color='#D97706'),yaxis='y2'))
            fig2.update_layout(height=280, barmode='group',
                               yaxis2=dict(overlaying='y',side='right',showgrid=False,title='달성률(%)'),
                               **CHART_LAYOUT)
            st.plotly_chart(fig2, use_container_width=True)

# ══════════════════════════════════════════════════════
# ⑤ INSIGHT WIDGETS
# ══════════════════════════════════════════════════════
st.markdown('<div id="sec-insight"></div>', unsafe_allow_html=True)
st.markdown('<div class="sec-hd">인사이트</div>', unsafe_allow_html=True)

ranked  = fdf[fdf['_ach'].notna()].copy()
worst10 = ranked.nsmallest(10,'_ach')
best10  = ranked.nlargest(10,'_ach')

def top10_html(rows):
    out = ''
    for i,(_, r) in enumerate(rows.iterrows(), 1):
        ach = r['_ach']
        clr = TL_INFO[r['_tl']]['fg']
        nm  = str(r.get('지표명',''))[:24]
        has_memo = '📝' if st.session_state.memos.get(r.get('KPI_ID','')) else ''
        out += f'<div class="t10"><span class="rk">{i}</span><span class="nm" title="{r.get("지표명","")}">{nm}{has_memo}</span><span class="vl" style="color:{clr}">{ach:.1f}%</span></div>'
    return out

w1, w2, w3 = st.columns(3)
with w1:
    st.markdown(f'<div class="wb"><h4>🔴 Worst Top 10 ({month}월)</h4>{top10_html(worst10)}</div>', unsafe_allow_html=True)
with w2:
    st.markdown(f'<div class="wb"><h4>🟢 Best Top 10 ({month}월)</h4>{top10_html(best10)}</div>',  unsafe_allow_html=True)
with w3:
    warn_rows = fdf[fdf['_warn']==True].sort_values('_delta')
    if not warn_rows.empty:
        whtml = ''
        for _,r in warn_rows.iterrows():
            nm  = str(r.get('지표명',''))[:22]
            dlt = r['_delta']
            whtml += f'<div class="t10"><span style="font-size:.7rem">⚠️</span><span class="nm">{nm}</span><span class="vl" style="color:#DC2626">▼{abs(dlt):.1f}%p</span><span style="color:{MUTED_FG};font-size:.7rem">{fmt_ach(r["_ach"])}</span></div>'
        st.markdown(f'<div class="wb"><h4>⚠️ 급락 경보 (-{WARN_DROP}%p↑, {len(warn_rows)}건)</h4>{whtml}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="wb"><h4>⚠️ 급락 경보</h4><div style="color:{MUTED_FG};padding:16px 0;text-align:center;font-size:.82rem">급락 KPI 없음 ✅</div></div>', unsafe_allow_html=True)

st.markdown('<div class="sec-hd" style="margin-top:1.25rem">분류별 분석</div>', unsafe_allow_html=True)
cat_cols = st.columns(3)
for col, cat in zip(cat_cols, CAT_ORDER):
    cat_rows = fdf[fdf['분류']==cat] if '분류' in fdf.columns else pd.DataFrame()
    with col:
        if cat_rows.empty:
            st.markdown(f'<div class="wb"><h4>{cat}</h4><div style="color:{MUTED_FG};font-size:.8rem;padding:8px 0">데이터 없음</div></div>', unsafe_allow_html=True)
            continue
        ct = len(cat_rows)
        ca = cat_rows['_ach'].dropna().mean()
        cc = {k: int((cat_rows['_tl']==k).sum()) for k in TL_INFO}
        items = ''
        for k in ['green','yellow','red']:
            n = cc[k]
            if n==0: continue
            pct = n/ct*100
            info = TL_INFO[k]
            items += f'<div class="cat-row"><span class="cat-nm">{info["dot"]}</span><div class="cat-bar-wrap"><div class="cat-bar" style="width:{pct:.0f}%;background:{info["fg"]}"></div></div><span style="font-size:.7rem;color:{info["fg"]};font-weight:600;width:56px;text-align:right">{n}건 {pct:.0f}%</span></div>'
        st.markdown(f'<div class="wb"><h4>{cat} — 평균 {ca:.1f}% / {ct}건</h4>{stk_html(cc,ct)}{items}</div>', unsafe_allow_html=True)

with st.expander('📋 데이터 요약'):
    s1,s2,s3,s4 = st.columns(4)
    s1.metric('전체 레코드', f'{len(df):,}건')
    s2.metric('선택 월 KPI', f'{len(mdf):,}건')
    s3.metric('필터 후 KPI', f'{len(fdf):,}건')
    s4.metric('저장된 메모', f'{len(st.session_state.memos)}건')
    if st.button('메모 전체 초기화', key='memo_clr'):
        st.session_state.memos = {}
        st.rerun()

    # ── Firestore 업로드 (Firebase 연결 시 표시) ─────────────────────────────
    if _fb_ready and st.session_state.logged_in:
        st.markdown(f'<hr style="border:none;border-top:1px solid {BORDER};margin:.75rem 0">', unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:.68rem;font-weight:600;color:{MUTED_FG};letter-spacing:.06em;text-transform:uppercase;margin-bottom:.5rem">🔥 Firestore 동기화</div>', unsafe_allow_html=True)
        up_col1, up_col2 = st.columns([3, 1])
        with up_col1:
            upload_file = st.file_uploader(
                'XLS → Firestore 업로드',
                type=['xls','xlsx','html'],
                key='fs_upload',
                label_visibility='collapsed',
                help='현재 로드된 XLS 파일을 Firestore kpi_2025 컬렉션에 업로드합니다.',
            )
        with up_col2:
            do_upload = st.button('업로드', key='fs_upload_btn', type='primary',
                                  use_container_width=True, disabled=upload_file is None)
        if do_upload and upload_file:
            with st.spinner('Firestore에 업로드 중...'):
                try:
                    raw_tbl  = load_data(upload_file.getvalue())
                    proc_df  = load_data_raw(raw_tbl)
                    n = fb.upload_kpi_df(proc_df)
                    st.success(f'✅ {n:,}건 업로드 완료. 페이지를 새로고침하면 Firestore 데이터로 전환됩니다.')
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f'업로드 실패: {e}')
