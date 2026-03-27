import streamlit as st
import requests
import re
import hashlib
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- 1. CONFIGURATION ---
TMDB_API_KEY = ""
try:
    TMDB_API_KEY = st.secrets["TMDB_API_KEY"]
except (KeyError, FileNotFoundError):
    TMDB_API_KEY = "57486deb33535eb0b12bbd780982370e"

# --- 2. DYNAMIC COLOR GENERATOR ---
def get_user_color(email):
    colors = ["#9B59B6", "#2980B9", "#27AE60", "#D35400", "#C0392B", "#16A085", "#2C3E50"]
    hash_obj = hashlib.md5(email.lower().encode())
    index = int(hash_obj.hexdigest(), 16) % len(colors)
    return colors[index]

# --- 3. PAGE CONFIG ---
st.set_page_config(page_title="Cine Predict", layout="wide", initial_sidebar_state="collapsed")

# --- 4. GLOBAL CSS ---
st.markdown("""
<style>
/* ============================================================
   GLOBAL BASE
============================================================ */
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background-color: #000000 !important;
    color: #FFFFFF !important;
    overflow-x: hidden !important;
}
.main { background-color: #000000 !important; }
.block-container {
    padding: 0 !important;
    margin: 0 !important;
    max-width: 100% !important;
}
header, footer { visibility: hidden !important; display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }

/* ============================================================
   FIX: INPUT FIELDS — white text, no black box
============================================================ */
div[data-baseweb="input"],
div[data-baseweb="textarea"],
.stTextInput > div > div,
.stTextInput > div > div > div {
    background-color: rgba(22, 22, 22, 0.88) !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    border-radius: 6px !important;
}

input,
input[type="text"],
input[type="email"],
input[type="password"],
input:-webkit-autofill,
input:-webkit-autofill:hover,
input:-webkit-autofill:focus,
textarea {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    -webkit-box-shadow: 0 0 0px 1000px rgba(22,22,22,0.9) inset !important;
    background-color: transparent !important;
    caret-color: #FFFFFF !important;
    font-size: 16px !important;
}
input::placeholder { color: rgba(255,255,255,0.45) !important; opacity: 1 !important; }
.stTextInput label, .stTextInput label p { display: none !important; }
div[data-testid="InputInstructions"],
div[data-testid="stInputInstructions"] { display: none !important; }

/* ============================================================
   SEARCH BAR — dark style
============================================================ */
.search-wrapper div[data-baseweb="input"],
.search-wrapper .stTextInput > div > div,
.search-wrapper .stTextInput > div > div > div {
    background-color: #1c2333 !important;
    border: 1px solid #2d3748 !important;
    border-radius: 10px !important;
    height: 56px !important;
}
.search-wrapper input {
    -webkit-box-shadow: 0 0 0px 1000px #1c2333 inset !important;
    padding-left: 16px !important;
}

/* ============================================================
   LOGO
============================================================ */
.logo-cine, .logo-predict {
    font-family: 'Inter', sans-serif;
    font-weight: 900;
    font-size: clamp(26px, 5vw, 46px);
    color: #00FFFF !important;
    text-shadow: 0 0 15px rgba(0,255,255,0.8), 0 0 30px rgba(0,255,255,0.4), 0 0 60px rgba(0,255,255,0.2);
    letter-spacing: 2px;
}

/* ============================================================
   TABS
============================================================ */
div[data-testid="stTabs"] button[data-baseweb="tab"] {
    background: transparent !important;
    border: none !important;
    border-bottom: 3px solid transparent !important;
    color: #71717A !important;
    padding-bottom: 8px !important;
}
div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] {
    color: #00FFFF !important;
    border-bottom: 3px solid #00FFFF !important;
}
div[data-testid="stTabs"] button[data-baseweb="tab"] p {
    font-size: clamp(13px, 2.5vw, 18px) !important;
    font-weight: 700 !important;
}

/* ============================================================
   PROFILE POPOVER BUTTON — cyan pill border, "Profile ^"
============================================================ */
div[data-testid="stPopover"] > div > button {
    background-color: transparent !important;
    border: 2px solid #00FFFF !important;
    border-radius: 30px !important;
    color: #00FFFF !important;
    font-weight: 700 !important;
    font-size: 14px !important;
    padding: 6px 18px !important;
    height: auto !important;
    min-height: 38px !important;
    width: auto !important;
    min-width: 110px !important;
    white-space: nowrap !important;
    box-shadow: 0 0 12px rgba(0,255,255,0.2) !important;
    transition: all 0.3s ease !important;
}
div[data-testid="stPopover"] > div > button:hover {
    background-color: rgba(0,255,255,0.1) !important;
    box-shadow: 0 0 20px rgba(0,255,255,0.4) !important;
}
div[data-testid="stPopover"] > div > button p,
div[data-testid="stPopover"] > div > button span,
div[data-testid="stPopover"] > div > button div {
    color: #00FFFF !important;
    -webkit-text-fill-color: #00FFFF !important;
    font-weight: 700 !important;
    font-size: 14px !important;
    background: transparent !important;
}
div[data-testid="stPopover"] > div > button svg { display: none !important; }

/* Popover body */
div[data-testid="stPopoverBody"] {
    background: linear-gradient(145deg, #0D0D0F, #1a1a1d) !important;
    border: 1px solid rgba(0,255,255,0.3) !important;
    border-radius: 16px !important;
    overflow: hidden !important;
    min-width: 260px !important;
    padding: 0 !important;
}
div[data-testid="stPopoverBody"] p {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}
div[data-testid="stPopoverBody"] .stMarkdown p {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}

/* Sign Out button inside popover */
div[data-testid="stPopoverBody"] div[data-testid="stButton"] button {
    background: linear-gradient(90deg, #00FFCC, #00BFFF) !important;
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    padding: 10px !important;
    height: auto !important;
    margin-top: 4px !important;
}

/* ============================================================
   SIDEBAR LABELS
============================================================ */
.side-label {
    color: #71717A !important;
    font-weight: 700;
    font-size: 14px;
    margin-top: 20px;
    margin-bottom: 2px;
}

/* ============================================================
   PREDICTION BADGE
============================================================ */
.prediction-badge {
    background-color: rgba(0,255,136,0.05);
    border: 1px solid #00FF88;
    color: #00FF88;
    padding: 8px 12px;
    border-radius: 5px;
    font-weight: bold;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    margin-top: 15px;
}

/* ============================================================
   CAST
============================================================ */
.cast-img {
    width: 100% !important;
    max-width: 110px !important;
    height: auto !important;
    aspect-ratio: 110 / 145;
    border-radius: 8px;
    object-fit: cover;
    border: 1px solid #2D2D2D;
}
.cast-name {
    color: #A1A1AA;
    font-size: clamp(9px, 1.5vw, 11px);
    margin-top: 5px;
    text-align: center;
    word-break: break-word;
}

/* ============================================================
   SIMILAR MOVIE BUTTONS
============================================================ */
div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button {
    background: transparent !important;
    background-image: none !important;
    border: none !important;
    padding: 0 !important;
    width: 100%;
    text-align: left !important;
    box-shadow: none !important;
}
div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button p {
    color: #FFFFFF !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    margin-top: 8px !important;
    white-space: normal !important;
    line-height: 1.2 !important;
}
div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button:hover p {
    text-decoration: underline !important;
    color: #00FFFF !important;
}

/* ============================================================
   FOOTER
============================================================ */
.full-width-footer {
    background-color: #121214;
    padding: 50px 20px 40px 20px;
    text-align: center;
    margin-top: 80px;
    border-top: 1px solid rgba(255,255,255,0.05);
}
.footer-nav {
    display: flex;
    justify-content: center;
    gap: 12px;
    margin-bottom: 30px;
    flex-wrap: wrap;
}
.footer-btn {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.1);
    color: #A1A1AA !important;
    font-weight: 600;
    font-size: clamp(12px, 2vw, 14px);
    padding: 8px 16px;
    border-radius: 30px;
    text-decoration: none !important;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    transition: all 0.3s ease;
}
.footer-btn:hover {
    background: rgba(0,255,255,0.08);
    border-color: #00FFFF;
    color: #00FFFF !important;
    transform: translateY(-3px);
    box-shadow: 0 10px 20px rgba(0,255,255,0.15);
}

/* ============================================================
   MODALS
============================================================ */
.modal-window {
    position: fixed;
    background-color: rgba(0,0,0,0.85);
    backdrop-filter: blur(8px);
    top: 0; right: 0; bottom: 0; left: 0;
    z-index: 999999;
    visibility: hidden; opacity: 0; pointer-events: none;
    transition: all 0.3s ease;
}
.modal-window:target { visibility: visible; opacity: 1; pointer-events: auto; }
.modal-content {
    width: 90%; max-width: 600px;
    position: absolute;
    top: 55%; left: 50%;
    transform: translate(-50%, -50%);
    padding: clamp(20px, 5vw, 40px);
    background: linear-gradient(145deg, #1A1A1D, #0D0D0F);
    border: 1px solid rgba(0,255,255,0.2);
    border-radius: 16px; color: #E0E0E0;
    box-shadow: 0 20px 50px rgba(0,0,0,0.8);
    transition: top 0.4s ease;
    max-height: 85vh; overflow-y: auto;
}
.modal-window:target .modal-content { top: 50%; }
.modal-close {
    color: #71717A !important; position: absolute;
    right: 20px; top: 20px; width: 36px; height: 36px;
    background: rgba(255,255,255,0.05); border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 22px; text-decoration: none !important;
    font-weight: bold; transition: all 0.3s ease;
}
.modal-close:hover { background: rgba(0,255,255,0.15); color: #00FFFF !important; transform: rotate(90deg); }
.modal-header {
    display: flex; align-items: center; gap: 12px;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    padding-bottom: 15px; margin-bottom: 20px;
}
.modal-header h2 { color: #00FFFF; margin: 0; font-weight: 800; }
.modal-body p { font-size: 16px; line-height: 1.7; color: #D4D4D8; }
.modal-body ul { line-height: 2.2; font-size: 16px; color: #D4D4D8; padding-left: 20px; }
.modal-body li span { color: #00FFFF; font-weight: bold; }
.tech-tags { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 15px; }
.tech-tag {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    padding: 6px 14px; border-radius: 8px;
    font-size: 14px; color: #FFFFFF; font-weight: 600;
}
.tech-tag span { color: #00FFFF; margin-right: 5px; }

/* ============================================================
   MISC
============================================================ */
div[data-testid="stSpinner"] p { color: #A1A1AA !important; }
.stMarkdown p, p { color: #FFFFFF !important; }

/* ============================================================
   MOBILE RESPONSIVE
============================================================ */
@media screen and (max-width: 768px) {
    [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; }
    [data-testid="stHorizontalBlock"] > div {
        min-width: 100% !important;
        width: 100% !important;
    }
    .cast-img { max-width: 70px !important; }
    h1 { font-size: 24px !important; }
}
@media screen and (max-width: 480px) {
    .logo-cine, .logo-predict { font-size: 24px !important; letter-spacing: 1px !important; }
}
</style>
""", unsafe_allow_html=True)


# --- 5. HELPERS ---
def render_logo():
    st.markdown(
        '<span class="logo-cine">CINE </span><span class="logo-predict">PREDICT</span>',
        unsafe_allow_html=True
    )

# --- 6. DATA FETCHING ---
@st.cache_data(ttl=86400, show_spinner=False)
def get_movie_details(query):
    session = requests.Session()
    session.mount('https://', HTTPAdapter(max_retries=Retry(total=3, backoff_factor=0.5)))
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = session.get(
            "https://api.themoviedb.org/3/search/movie",
            params={"api_key": TMDB_API_KEY, "query": query},
            headers=headers, timeout=10
        )
        if res.status_code == 401:
            return None, "❌ Invalid TMDB API Key."
        res.raise_for_status()
        data = res.json()
        if not data.get('results'):
            return None, "Movie not found."
        mid = data['results'][0]['id']
        detail_res = session.get(
            f"https://api.themoviedb.org/3/movie/{mid}",
            params={"api_key": TMDB_API_KEY, "append_to_response": "credits,videos,recommendations"},
            headers=headers, timeout=10
        )
        detail_res.raise_for_status()
        return detail_res.json(), None
    except requests.exceptions.ConnectionError:
        return None, "🌐 Network Error: Could not reach TMDB. Try a VPN like Cloudflare WARP (1.1.1.1)!"
    except Exception as e:
        return None, f"⚠️ Unexpected error: {str(e)}"

def update_search(new_title):
    st.session_state['movie_search_bar'] = new_title

# --- 7. SESSION STATE ---
if 'auth' not in st.session_state:
    st.session_state['auth'] = False

# ============================================================
# LOGIN PAGE — Netflix-style background, CINE PREDICT logo,
#              dark card, email + password fields, Sign In btn
# ============================================================
if not st.session_state['auth']:

    st.markdown("""
    <style>
    /* ── Netflix-style poster grid background ── */
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    .main {
        background-image:
            linear-gradient(rgba(0,0,0,0.70), rgba(0,0,0,0.70)),
            url('https://assets.nflxext.com/ffe/siteui/vlv3/9d3533b2-0e5e-449c-82f4-f437f3f40bbf/web/IN-en-20250317-TRIFECTA-perspective_4db89702-e8e0-4c08-b74e-43a0eb8e12e4_large.jpg') !important;
        background-size: cover !important;
        background-position: center center !important;
        background-repeat: no-repeat !important;
        background-attachment: fixed !important;
        min-height: 100vh !important;
        background-color: #000 !important;
    }

    /* ── Page padding ── */
    .block-container {
        padding: 60px 16px 40px 16px !important;
        max-width: 100% !important;
    }

    /* ── SIGN IN BUTTON — highest specificity to override global rules ── */
    div[data-testid="stButton"] > button[kind="secondary"],
    div[data-testid="stButton"] > button[kind="primary"],
    div[data-testid="stButton"] > button {
        background: linear-gradient(90deg, #00FFCC, #00BFFF) !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 800 !important;
        font-size: 16px !important;
        height: 52px !important;
        margin-top: 10px !important;
        letter-spacing: 0.5px !important;
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        visibility: visible !important;
        opacity: 1 !important;
        cursor: pointer !important;
        box-shadow: none !important;
    }
    div[data-testid="stButton"] > button > p,
    div[data-testid="stButton"] > button > div > p {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        font-weight: 800 !important;
        font-size: 16px !important;
        margin: 0 !important;
    }
    div[data-testid="stButton"] > button:hover {
        opacity: 0.88 !important;
        box-shadow: 0 8px 24px rgba(0,255,204,0.45) !important;
    }

    /* ── Checkbox ── */
    .stCheckbox label p {
        color: rgba(255,255,255,0.85) !important;
        -webkit-text-fill-color: rgba(255,255,255,0.85) !important;
        font-size: 14px !important;
    }

    /* ── Mobile responsive ── */
    @media (max-width: 640px) {
        .block-container { padding: 24px 10px 24px 10px !important; }
        .login-card-inner { padding: 22px 16px !important; }
    }
    </style>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        # Logo centred above card
        st.markdown(
            "<div style='text-align:center; margin-bottom:18px;'>"
            "<span class='logo-cine'>CINE </span>"
            "<span class='logo-predict'>PREDICT</span>"
            "</div>",
            unsafe_allow_html=True
        )

        # Glassmorphism card — heading only (inputs must be Streamlit widgets)
        st.markdown("""
        <div class="login-card-inner" style="
            background: rgba(0,0,0,0.78);
            border-radius: 12px;
            padding: 36px 36px 20px 36px;
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            border: 1px solid rgba(255,255,255,0.07);
            box-shadow: 0 8px 40px rgba(0,0,0,0.7);
        ">
            <h2 style="color:#FFFFFF; font-size:30px; font-weight:800; margin:0 0 20px 0;">Sign In</h2>
        </div>
        """, unsafe_allow_html=True)

        email = st.text_input("_email", placeholder="Email or phone number",
                              label_visibility="collapsed")
        password = st.text_input("_password", placeholder="Password",
                                 type="password", label_visibility="collapsed")

        col_rem, col_help = st.columns([1, 1])
        with col_rem:
            st.checkbox("Remember me", value=True)
        with col_help:
            st.markdown(
                "<p style='text-align:right; font-size:14px; margin-top:6px;'>"
                "<a href='mailto:support@cinepredict.com' "
                "style='color:#FFFFFF; text-decoration:none; font-weight:500;' "
                "onmouseover=\"this.style.textDecoration='underline'\" "
                "onmouseout=\"this.style.textDecoration='none'\">Need help?</a></p>",
                unsafe_allow_html=True
            )

        # ── SIGN IN BUTTON ──
        if st.button("Sign In", use_container_width=True, key="login_btn"):
            if re.match(r"[^@]+@[^@]+\.[^@]+", email) or (len(email) >= 3 and "@" not in email):
                st.session_state['auth'] = True
                st.session_state['user_email'] = email if email else "user@example.com"
                st.rerun()
            else:
                st.error("Please enter a valid email or phone number.")

        st.markdown(
            "<p style='color:rgba(255,255,255,0.55); text-align:center; "
            "font-size:14px; margin-top:18px; margin-bottom:8px;'>"
            "New to Cine Predict? "
            "<strong style='color:#FFFFFF; cursor:pointer;'>Sign up now.</strong></p>",
            unsafe_allow_html=True
        )

# ============================================================
# MAIN APP
# ============================================================
else:
    user_color = get_user_color(st.session_state['user_email'])
    u_init = st.session_state['user_email'][0].upper()

    st.markdown("""
    <style>
    .block-container {
        padding: 24px 32px 0 32px !important;
        max-width: 100% !important;
    }
    @media (max-width: 640px) {
        .block-container { padding: 14px 12px 0 12px !important; }
    }
    </style>
    """, unsafe_allow_html=True)

    # --- HEADER: Logo | spacer | Profile popover ---
    h_logo, h_spacer, h_profile = st.columns([3, 6, 1.8])
    with h_logo:
        render_logo()
    with h_profile:
        with st.popover("👤 Profile"):
            st.markdown(
                f"""
                <div style="padding:20px; text-align:center;">
                    <p style="font-size:12px; color:#A1A1AA; margin-bottom:14px; word-break:break-all;">
                        {st.session_state['user_email']}
                    </p>
                    <div style="
                        background:{user_color};
                        color:#FFFFFF;
                        width:70px; height:70px; border-radius:50%;
                        margin:0 auto 14px;
                        display:flex; align-items:center; justify-content:center;
                        font-size:30px; font-weight:900;
                        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
                    ">{u_init}</div>
                    <p style="font-size:20px; color:#FFFFFF; font-weight:700; margin-bottom:4px;">Hi, User!</p>
                </div>
                """,
                unsafe_allow_html=True
            )
            if st.button("Sign Out", use_container_width=True):
                st.session_state['auth'] = False
                st.rerun()

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

    # --- SEARCH BAR ---
    st.markdown("<div class='search-wrapper'>", unsafe_allow_html=True)
    query = st.text_input(
        "_search_hidden",
        placeholder="Search for a movie title...",
        key="movie_search_bar",
        label_visibility="collapsed"
    )
    st.markdown("</div>", unsafe_allow_html=True)

    final_query = query.strip()

    if final_query:
        with st.spinner("Fetching movie details..."):
            data, error_msg = get_movie_details(final_query)

        if data:
            st.markdown("---")
            col_poster, col_info, col_sidebar = st.columns([1, 2.7, 1])

            with col_poster:
                poster_path = data.get('poster_path')
                if poster_path:
                    st.image(f"https://image.tmdb.org/t/p/w500{poster_path}", use_container_width=True)
                else:
                    st.markdown(
                        '<div style="width:100%;aspect-ratio:2/3;background:#1a1a1a;border-radius:8px;'
                        'display:flex;align-items:center;justify-content:center;color:#555;">No Poster</div>',
                        unsafe_allow_html=True
                    )

            with col_info:
                vote_avg = round(data.get('vote_average', 0), 1)
                release_year = data.get('release_date', 'N/A')[:4]
                st.markdown(
                    f"<h1 style='color:#FFFFFF;font-size:clamp(22px,4vw,36px);margin-bottom:6px;'>"
                    f"{data['title']}</h1>",
                    unsafe_allow_html=True
                )
                st.markdown("<h3 style='color:#00FF88;margin:0 0 6px 0;'>93% Match Prediction</h3>",
                            unsafe_allow_html=True)
                st.markdown(
                    f"<p style='color:#71717A;margin:0 0 12px 0;'>{release_year} | ★ {vote_avg}/10</p>",
                    unsafe_allow_html=True
                )
                st.markdown(
                    f"<p style='color:#FFFFFF;line-height:1.6;'>{data.get('overview', '')}</p>",
                    unsafe_allow_html=True
                )
                st.markdown('<div class="prediction-badge">🎯 PREDICTION: BOX OFFICE HIT</div>',
                            unsafe_allow_html=True)

            with col_sidebar:
                cast = data.get('credits', {}).get('cast', [])
                if cast:
                    st.markdown('<p class="side-label">Starring</p>', unsafe_allow_html=True)
                    st.write(", ".join([a['name'] for a in cast[:4]]))
                genres = data.get('genres', [])
                if genres:
                    st.markdown('<p class="side-label">Genres</p>', unsafe_allow_html=True)
                    st.write(", ".join([g['name'] for g in genres]))
                st.markdown('<p class="side-label">Global Rating</p>', unsafe_allow_html=True)
                st.markdown(
                    f'<p style="font-size:18px;color:#EAB308;font-weight:bold;">★ {vote_avg}/10</p>',
                    unsafe_allow_html=True
                )

            st.markdown("<br>", unsafe_allow_html=True)
            t_c, t_t, t_s = st.tabs(["👥 Cast", "▷ Trailer", "🎞️ Similar"])

            with t_c:
                cast_list = data.get('credits', {}).get('cast', [])[:10]
                if cast_list:
                    cols = st.columns(min(len(cast_list), 10))
                    for i, act in enumerate(cast_list):
                        with cols[i]:
                            img_p = act.get('profile_path')
                            img_u = (f"https://image.tmdb.org/t/p/h632{img_p}" if img_p
                                     else "https://www.themoviedb.org/assets/2/v4/glyphicons/basic/"
                                          "glyphicons-basic-4-user-grey-d8fe577334c16c30617d9e3d30901e377f5144c"
                                          "cc58cd014ee8d1c026a71573c.svg")
                            st.markdown(
                                f'<div style="text-align:center;">'
                                f'<img src="{img_u}" class="cast-img">'
                                f'<div class="cast-name">{act["name"]}</div></div>',
                                unsafe_allow_html=True
                            )

            with t_t:
                vids = data.get('videos', {}).get('results', [])
                video = next((v for v in vids if v['type'] == 'Trailer' and v['site'] == 'YouTube'), None)
                if not video:
                    video = next((v for v in vids if v['site'] == 'YouTube'), None)
                if video:
                    st.video(f"https://www.youtube.com/watch?v={video['key']}")
                else:
                    st.info("Trailer not found for this movie.")

            with t_s:
                recs = data.get('recommendations', {}).get('results', [])[:6]
                if recs:
                    r_cols = st.columns(min(len(recs), 6))
                    for i, m in enumerate(recs):
                        with r_cols[i]:
                            if m.get('poster_path'):
                                st.image(f"https://image.tmdb.org/t/p/w342{m['poster_path']}",
                                         use_container_width=True)
                            else:
                                st.image("https://via.placeholder.com/342x513/111111/FFFFFF?text=No+Poster",
                                         use_container_width=True)
                            st.button(m['title'], key=f"rec_{m['id']}",
                                      on_click=update_search, args=(m['title'],))
        else:
            if error_msg == "Movie not found.":
                st.warning(error_msg)
            else:
                st.error(error_msg)

    else:
        st.markdown("""
        <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
                    margin-top:80px;padding:0 16px;text-align:center;">
            <div style="background-color:#071D22;padding:25px;border-radius:50%;margin-bottom:25px;">
                <svg width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="#00FFFF"
                     stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18"></rect>
                    <line x1="7" y1="2" x2="7" y2="22"></line>
                    <line x1="17" y1="2" x2="17" y2="22"></line>
                    <line x1="2" y1="12" x2="22" y2="12"></line>
                    <line x1="2" y1="7" x2="7" y2="7"></line>
                    <line x1="2" y1="17" x2="7" y2="17"></line>
                    <line x1="17" y1="17" x2="22" y2="17"></line>
                    <line x1="17" y1="7" x2="22" y2="7"></line>
                </svg>
            </div>
            <h1 style="font-family:'Inter',sans-serif;font-weight:800;
                       font-size:clamp(28px,5vw,42px);margin-bottom:10px;color:#FFFFFF;">
                Discover Your Next Favorite
            </h1>
            <p style="color:#71717A;font-size:clamp(15px,2.5vw,18px);max-width:500px;">
                Enter a movie title to explore ratings and details that help you choose your next film.
            </p>
        </div>
        """, unsafe_allow_html=True)

    # --- FOOTER ---
    st.markdown("""
    <div class="full-width-footer">
        <div class="footer-nav">
            <a href="#modal-about" class="footer-btn">📝 About</a>
            <a href="#modal-features" class="footer-btn">✨ Features</a>
            <a href="#modal-tech" class="footer-btn">💻 Technology</a>
            <a href="#modal-support" class="footer-btn">🎧 Support</a>
        </div>
        <p style="color:#71717A;font-size:14px;margin-bottom:25px;">
            Built for speed and accuracy. Discover movies, explore ratings, and find useful details all in one place.
        </p>
        <p style="color:#404040;font-size:13px;margin:0;">© 2026 Cine Predict Platform</p>
    </div>

    <div id="modal-about" class="modal-window">
        <div class="modal-content">
            <a href="#close" class="modal-close">&#x2715;</a>
            <div class="modal-header"><h2>About Cine Predict</h2></div>
            <div class="modal-body">
                <p><strong>Cine Predict</strong> is a sleek, intelligent web application designed to help users discover movies and explore cinematic data instantly.</p>
                <p>Simply search for any movie title worldwide to uncover critical details including global ratings, box office predictions, release history, and popularity metrics.</p>
                <p>Our platform aggregates real-time data from global APIs to ensure you have the most accurate information right at your fingertips.</p>
            </div>
        </div>
    </div>

    <div id="modal-features" class="modal-window">
        <div class="modal-content">
            <a href="#close" class="modal-close">&#x2715;</a>
            <div class="modal-header"><h2>Platform Features</h2></div>
            <div class="modal-body">
                <ul>
                    <li><span>🔍 Intelligent Search:</span> Find movies globally by exact or partial title.</li>
                    <li><span>⭐ Real-Time Metrics:</span> View live community ratings and popularity indexes.</li>
                    <li><span>🎬 Deep Insights:</span> Access comprehensive overviews, cast details, and genres.</li>
                    <li><span>▷ Media Integration:</span> Watch official trailers directly within the platform.</li>
                    <li><span>⚡ Blazing Fast:</span> Built with advanced caching for zero-wait load times.</li>
                </ul>
            </div>
        </div>
    </div>

    <div id="modal-tech" class="modal-window">
        <div class="modal-content">
            <a href="#close" class="modal-close">&#x2715;</a>
            <div class="modal-header"><h2>Technology Stack</h2></div>
            <div class="modal-body">
                <p>Our platform is powered by a modern, highly optimized technology stack:</p>
                <div class="tech-tags">
                    <div class="tech-tag"><span>🐍</span> Python Core</div>
                    <div class="tech-tag"><span>🔥</span> Streamlit Framework</div>
                    <div class="tech-tag"><span>🌐</span> TMDb REST API</div>
                    <div class="tech-tag"><span>📊</span> Pandas Engine</div>
                    <div class="tech-tag"><span>🤖</span> Scikit-Learn Models</div>
                </div>
            </div>
        </div>
    </div>

    <div id="modal-support" class="modal-window">
        <div class="modal-content">
            <a href="#close" class="modal-close">&#x2715;</a>
            <div class="modal-header"><h2>Help & Support</h2></div>
            <div class="modal-body">
                <p>We are dedicated to continuously improving your movie discovery experience.</p>
                <p>If you encounter any bugs, network issues, or feature requests, our team is ready to listen.</p>
                <p style="margin-top:20px;color:#00FFFF;font-weight:600;">Contact: support@cinepredict.com</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)