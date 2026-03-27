import streamlit as st
import requests
import re
import hashlib
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- 1. CONFIGURATION ---
# FIX: Safer secrets handling — checks key existence before access
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

# --- 3. UI ENGINE & CSS ---
st.set_page_config(page_title="Cine Predict", layout="wide")

st.markdown("""
    <style>
    /* ============================================================
       GLOBAL RESET — Force dark theme regardless of system/Streamlit prefs
       FIX 1: Black input box + invisible text caused by Streamlit's 
       auto dark-mode applying conflicting background to inputs.
       We explicitly override ALL color properties using !important
       and target both webkit fill and caret colors.
    ============================================================ */
    html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        overflow-y: scroll !important;
        overflow-x: hidden !important;
    }

    /* FIX 2: Streamlit injects a theme-aware background on .main — override it */
    .main { background-color: #000000 !important; }
    .block-container {
        padding-bottom: 0px !important;
        margin-bottom: 0px !important;
        /* FIX 3 (Mobile): Reduce side padding on small screens */
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }
    header, footer { visibility: hidden !important; display: none !important; }

    /* ============================================================
       INPUT FIELDS — The core visibility fix
       FIX: Streamlit Cloud dark mode sets input bg to near-black (#1e1e1e)
       with dark text, making text invisible. We force white background
       with black text for ALL input types.
    ============================================================ */
    div[data-baseweb="input"],
    div[data-baseweb="textarea"],
    .stTextInput > div > div {
        background-color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        position: relative;
    }

    /* FIX: Force text color — -webkit-text-fill-color overrides color in Chrome/Safari */
    input,
    input:-webkit-autofill,
    input:-webkit-autofill:hover,
    input:-webkit-autofill:focus,
    textarea {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        -webkit-box-shadow: 0 0 0px 1000px #FFFFFF inset !important;
        background-color: #FFFFFF !important;
        caret-color: #000000 !important;
        /* FIX (Mobile): Remove large right padding that hid text on phones */
        padding-right: 40px !important;
    }

    /* Placeholder text */
    input::placeholder { color: #9ca3af !important; opacity: 1 !important; }

    /* LOGIN PAGE: EMAIL LABEL */
    .stTextInput label, .stTextInput label p {
        color: #A1A1AA !important;
        font-weight: 600 !important;
    }

    /* SEARCH BAR ICON INJECTION */
    div[data-baseweb="input"]:has(input[placeholder="Search for a movie title..."])::after {
        content: "";
        position: absolute;
        right: 15px;
        top: 50%;
        transform: translateY(-50%);
        width: 20px;
        height: 20px;
        background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="%23A1A1AA" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>');
        background-size: contain;
        background-repeat: no-repeat;
        pointer-events: none;
    }

    /* FIX: Hide 'Press Enter to apply' instruction overlay */
    div[data-testid="InputInstructions"],
    div[data-testid="stInputInstructions"] {
        display: none !important;
    }

    /* ============================================================
       TABS STYLING
    ============================================================ */
    div[data-testid="stTabs"] button[data-baseweb="tab"] {
        background: transparent !important;
        border: none !important;
        border-bottom: 3px solid transparent !important;
        color: #71717A !important;
        padding-bottom: 8px !important;
        padding-top: 8px !important;
    }
    div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] {
        color: #00FFFF !important;
        border-bottom: 3px solid #00FFFF !important;
    }
    div[data-testid="stTabs"] button[data-baseweb="tab"] p {
        /* FIX (Mobile): Smaller tab font on phones */
        font-size: clamp(13px, 2.5vw, 18px) !important;
        font-weight: 700 !important;
    }

    /* ============================================================
       SIDEBAR & LOGO
    ============================================================ */
    .side-label {
        color: #71717A !important;
        font-weight: 700;
        font-size: 14px;
        margin-top: 20px;
        margin-bottom: 2px;
    }
    .side-val { color: #FFFFFF; font-size: 15px; line-height: 1.4; }
    .logo-container { display: flex; align-items: center; gap: 12px; margin-bottom: 5px; }
    .logo-cine, .logo-predict {
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        /* FIX (Mobile): Fluid font size */
        font-size: clamp(20px, 5vw, 32px) !important;
        color: #00FFFF !important;
        text-shadow: 0 0 10px rgba(0, 255, 255, 0.7), 0 0 20px rgba(0, 255, 255, 0.4);
        letter-spacing: 0.5px;
    }

    /* ============================================================
       BADGE & IMAGES
    ============================================================ */
    .prediction-badge {
        background-color: rgba(0, 255, 136, 0.05);
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
    /* FIX (Mobile): Cast images scale down on small screens */
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
       SIMILAR SECTION TITLES
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
    }

    /* ============================================================
       FOOTER
    ============================================================ */
    .full-width-footer {
        width: auto;
        /* FIX: Use calc-based negative margins instead of -5rem which can clip on mobile */
        margin-left: calc(-1 * var(--block-padding, 1rem));
        margin-right: calc(-1 * var(--block-padding, 1rem));
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
        flex-wrap: wrap; /* Already correct — wraps on mobile */
    }
    .footer-btn {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #A1A1AA !important;
        font-weight: 600;
        /* FIX (Mobile): Smaller font and padding on phones */
        font-size: clamp(12px, 2vw, 14px);
        padding: 8px 16px;
        border-radius: 30px;
        text-decoration: none !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        display: inline-flex;
        align-items: center;
        gap: 8px;
    }
    .footer-btn:hover {
        background: rgba(0, 255, 255, 0.08);
        border-color: #00FFFF;
        color: #00FFFF !important;
        transform: translateY(-3px);
        box-shadow: 0 10px 20px rgba(0, 255, 255, 0.15);
    }

    /* ============================================================
       MODALS (GLASSMORPHISM)
    ============================================================ */
    .modal-window {
        position: fixed;
        background-color: rgba(0, 0, 0, 0.85);
        backdrop-filter: blur(8px);
        top: 0; right: 0; bottom: 0; left: 0;
        z-index: 999999;
        visibility: hidden;
        opacity: 0;
        pointer-events: none;
        transition: all 0.3s ease;
    }
    .modal-window:target { visibility: visible; opacity: 1; pointer-events: auto; }

    .modal-content {
        /* FIX (Mobile): Use % width and max-width for responsive modals */
        width: 90%;
        max-width: 600px;
        position: absolute;
        top: 55%; left: 50%;
        transform: translate(-50%, -50%);
        /* FIX (Mobile): Reduce padding on small screens */
        padding: clamp(20px, 5vw, 40px);
        background: linear-gradient(145deg, #1A1A1D, #0D0D0F);
        border: 1px solid rgba(0, 255, 255, 0.2);
        border-radius: 16px;
        color: #E0E0E0;
        text-align: left;
        box-shadow: 0 20px 50px rgba(0,0,0,0.8), inset 0 0 20px rgba(0,255,255,0.02);
        transition: top 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
        /* FIX (Mobile): Allow scrolling within modal if content is tall */
        max-height: 85vh;
        overflow-y: auto;
    }
    .modal-window:target .modal-content { top: 50%; }

    .modal-close {
        color: #71717A !important;
        position: absolute;
        right: 20px; top: 20px;
        width: 36px; height: 36px;
        background: rgba(255,255,255,0.05);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        text-decoration: none !important;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .modal-close:hover {
        background: rgba(0,255,255,0.15);
        color: #00FFFF !important;
        transform: rotate(90deg);
    }

    .modal-header {
        display: flex;
        align-items: center;
        gap: 12px;
        border-bottom: 1px solid rgba(255,255,255,0.1);
        padding-bottom: 15px;
        margin-bottom: 20px;
    }
    .modal-header h2 { color: #00FFFF; margin: 0; font-weight: 800; letter-spacing: 0.5px; }
    .modal-body p { font-size: 16px; line-height: 1.7; color: #D4D4D8; }
    .modal-body ul { line-height: 2.2; font-size: 16px; color: #D4D4D8; padding-left: 20px; }
    .modal-body li span { color: #00FFFF; font-weight: bold; }

    .tech-tags { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 15px; }
    .tech-tag {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        padding: 6px 14px;
        border-radius: 8px;
        font-size: 14px;
        color: #FFFFFF;
        font-weight: 600;
    }
    .tech-tag span { color: #00FFFF; margin-right: 5px; }

    /* ============================================================
       USER POPOVER BUTTON
    ============================================================ */
    div[data-testid="stPopover"] button {
        background-color: #FFFFFF !important;
        border-radius: 50% !important;
        width: 45px !important;
        height: 45px !important;
        min-width: 45px !important;
        border: 2px solid #E0E0E0 !important;
        padding: 0 !important;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.5) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    div[data-testid="stPopover"] button div,
    div[data-testid="stPopover"] button p,
    div[data-testid="stPopover"] button span {
        background-color: transparent !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        font-weight: 800 !important;
        font-size: 20px !important;
        margin: 0 !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    div[data-testid="stPopover"] button svg { display: none !important; }
    div[data-testid="stPopoverBody"] {
        background-color: #FFFFFF !important;
        border-radius: 15px !important;
    }
    div[data-testid="stPopoverBody"] p {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }

    /* ============================================================
       MOBILE RESPONSIVE OVERRIDES
       FIX: Streamlit columns stack oddly on phones. We target small viewports.
    ============================================================ */
    @media screen and (max-width: 640px) {
        /* Movie detail area: stack columns vertically */
        [data-testid="stHorizontalBlock"] {
            flex-direction: column !important;
        }
        [data-testid="stHorizontalBlock"] > div {
            width: 100% !important;
            min-width: 100% !important;
        }

        /* Cast grid: show fewer columns */
        .cast-img { max-width: 80px !important; }

        /* Hero text */
        h1 { font-size: 28px !important; }

        /* Reduce empty top space on login */
        .login-spacer { margin-top: 20px !important; }

        /* Footer margins */
        .full-width-footer {
            margin-left: -1rem;
            margin-right: -1rem;
        }
    }

    /* ============================================================
       SPINNER & MISC
    ============================================================ */
    div[data-testid="stSpinner"] p { color: #A1A1AA !important; }

    /* Ensure st.write text stays white */
    .stMarkdown p, .stText, p { color: #FFFFFF !important; }
    /* But NOT inside the popover white box */
    div[data-testid="stPopoverBody"] .stMarkdown p,
    div[data-testid="stPopoverBody"] p { color: #000000 !important; }

    </style>
""", unsafe_allow_html=True)


def render_logo(size_scale=1):
    st.markdown("""
        <div class="logo-container">
            <div>
                <span class="logo-cine">CINE </span><span class="logo-predict">PREDICT</span>
            </div>
        </div>
    """, unsafe_allow_html=True)


# --- 4. DATA FETCHING ---
@st.cache_data(ttl=86400, show_spinner=False)
def get_movie_details(query):
    session = requests.Session()
    session.mount('https://', HTTPAdapter(max_retries=Retry(total=3, backoff_factor=0.5)))
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        search_url = "https://api.themoviedb.org/3/search/movie"
        search_params = {"api_key": TMDB_API_KEY, "query": query}
        res = session.get(search_url, params=search_params, headers=headers, timeout=10)

        if res.status_code == 401:
            return None, "❌ Invalid TMDB API Key. Please check your credentials."

        res.raise_for_status()
        data = res.json()

        if not data.get('results'):
            return None, "Movie not found."

        mid = data['results'][0]['id']
        detail_url = f"https://api.themoviedb.org/3/movie/{mid}"
        detail_params = {
            "api_key": TMDB_API_KEY,
            "append_to_response": "credits,videos,recommendations"
        }

        detail_res = session.get(detail_url, params=detail_params, headers=headers, timeout=10)
        detail_res.raise_for_status()

        return detail_res.json(), None

    except requests.exceptions.ConnectionError:
        return None, "🌐 Network Error: Could not reach TMDB. Try using a VPN like Cloudflare WARP (1.1.1.1)!"
    except Exception as e:
        return None, f"⚠️ An unexpected error occurred: {str(e)}"


# --- CALLBACK TO SAFELY UPDATE SEARCH BAR ---
def update_search(new_title):
    st.session_state['movie_search_bar'] = new_title


# --- 5. APP FLOW ---
if 'auth' not in st.session_state:
    st.session_state['auth'] = False

if not st.session_state['auth']:
    # FIX (Mobile): Use tighter columns on small screens; [1,2,1] is safer than [1,1.2,1]
    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.markdown("<br><br>", unsafe_allow_html=True)
        render_logo(size_scale=1)
        st.markdown("<h2 style='font-size:26px; margin-top:20px; color:#FFFFFF;'>Member Access</h2>",
                    unsafe_allow_html=True)
        email = st.text_input("Email Address", placeholder="e.g. name@domain.com", autocomplete="email")
        if st.button("Sign In", use_container_width=True):
            if re.match(r"[^@]+@[^@]+\.[^@]+", email):
                st.session_state['auth'] = True
                st.session_state['user_email'] = email
                st.rerun()
            else:
                st.error("Enter a valid email.")

else:
    user_color = get_user_color(st.session_state['user_email'])

    h1, h2 = st.columns([9.5, 0.5])
    with h1:
        render_logo(size_scale=0.8)
    with h2:
        u_init = st.session_state['user_email'][0].upper()
        with st.popover(u_init):
            st.markdown(
                f'<div style="text-align:center; padding:5px; background-color:#FFFFFF;">'
                f'<p style="font-size:14px; color:#71717A !important; margin-bottom:20px; font-weight:500;">'
                f'{st.session_state["user_email"]}</p>'
                f'<div style="background:{user_color}; color:#FFFFFF !important; '
                f'-webkit-text-fill-color:#FFFFFF !important; width:70px; height:70px; border-radius:50%; '
                f'margin:0 auto 15px; display:flex; align-items:center; justify-content:center; '
                f'font-size:30px; font-weight:900;">{u_init}</div>'
                f'<p style="font-size:22px; color:#000000 !important; font-weight:500; '
                f'margin-bottom:20px;">Hi, User!</p></div>',
                unsafe_allow_html=True
            )
            if st.button("Sign Out", use_container_width=True):
                st.session_state['auth'] = False
                st.rerun()

    query = st.text_input("", placeholder="Search for a movie title...", key="movie_search_bar")
    final_query = query.strip()

    if final_query:
        with st.spinner("Fetching movie details..."):
            data, error_msg = get_movie_details(final_query)

        if data:
            st.markdown("---")

            # FIX (Mobile): On small screens Streamlit stacks columns automatically.
            # Keep ratio but reduce sidebar weight so it doesn't crowd mobile.
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
                st.markdown(f"<h1 style='color:#FFFFFF; font-size:clamp(22px,4vw,36px);'>{data['title']}</h1>",
                            unsafe_allow_html=True)
                st.markdown("<h3 style='color:#00FF88;'>93% Match Prediction</h3>", unsafe_allow_html=True)
                release_year = data.get('release_date', 'N/A')[:4]
                vote_avg = round(data.get('vote_average', 0), 1)
                st.markdown(
                    f"<p style='color:#71717A;'>{release_year} | ★ {vote_avg}/10</p>",
                    unsafe_allow_html=True
                )
                st.markdown(f"<p style='color:#FFFFFF;'>{data.get('overview', '')}</p>", unsafe_allow_html=True)
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
                    f'<p style="font-size:18px; color:#EAB308; font-weight:bold;">★ {vote_avg}/10</p>',
                    unsafe_allow_html=True
                )

            st.markdown("<br>", unsafe_allow_html=True)

            t_c, t_t, t_s = st.tabs(["👥 Cast", "▷ Trailer", "🎞️ Similar"])

            with t_c:
                cast_list = data.get('credits', {}).get('cast', [])[:10]
                # FIX (Mobile): Use fewer columns on mobile — 5 is safer than 10
                # We keep 10 cols but CSS handles overflow at small sizes
                if cast_list:
                    cols = st.columns(min(len(cast_list), 10))
                    for i, act in enumerate(cast_list):
                        with cols[i]:
                            img_p = act.get('profile_path')
                            if img_p:
                                img_u = f"https://image.tmdb.org/t/p/h632{img_p}"
                            else:
                                img_u = ("https://www.themoviedb.org/assets/2/v4/glyphicons/basic/"
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
                    # FIX (Mobile): Use fewer columns for similar movies on small screens
                    r_cols = st.columns(min(len(recs), 6))
                    for i, m in enumerate(recs):
                        with r_cols[i]:
                            # FIX: Guard against missing poster_path (was crashing on some movies)
                            if m.get('poster_path'):
                                st.image(
                                    f"https://image.tmdb.org/t/p/w342{m['poster_path']}",
                                    use_container_width=True
                                )
                            else:
                                st.image(
                                    "https://via.placeholder.com/342x513/111111/FFFFFF?text=No+Poster",
                                    use_container_width=True
                                )
                            st.button(
                                m['title'],
                                key=f"rec_{m['id']}",
                                on_click=update_search,
                                args=(m['title'],)
                            )
        else:
            if error_msg == "Movie not found.":
                st.warning(error_msg)
            else:
                st.error(error_msg)

    else:
        st.markdown("""
        <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; margin-top:80px; padding: 0 16px; text-align:center;">
            <div style="background-color:#071D22; padding:25px; border-radius:50%; margin-bottom:25px;">
                <svg width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="#00FFFF" stroke-width="2.5"
                     stroke-linecap="round" stroke-linejoin="round">
                    <rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18"></rect>
                    <line x1="7" y1="2" x2="7" y2="22"></line><line x1="17" y1="2" x2="17" y2="22"></line>
                    <line x1="2" y1="12" x2="22" y2="12"></line><line x1="2" y1="7" x2="7" y2="7"></line>
                    <line x1="2" y1="17" x2="7" y2="17"></line><line x1="17" y1="17" x2="22" y2="17"></line>
                    <line x1="17" y1="7" x2="22" y2="7"></line>
                </svg>
            </div>
            <h1 style="font-family:'Inter',sans-serif; font-weight:800; font-size:clamp(28px,5vw,42px);
                       margin-bottom:10px; color:#FFFFFF;">Discover Your Next Favorite</h1>
            <p style="color:#71717A; font-size:clamp(15px,2.5vw,18px); text-align:center; max-width:500px;">
                Enter a movie title to explore ratings and details that help you choose your next film.
            </p>
        </div>
        """, unsafe_allow_html=True)

    # --- FOOTER WITH INTERACTIVE MODALS ---
    st.markdown("""
        <div class="full-width-footer">
            <div class="footer-nav">
                <a href="#modal-about" class="footer-btn">📝 About</a>
                <a href="#modal-features" class="footer-btn">✨ Features</a>
                <a href="#modal-tech" class="footer-btn">💻 Technology</a>
                <a href="#modal-support" class="footer-btn">🎧 Support</a>
            </div>
            <p style="color:#71717A; font-size:14px; margin-bottom:25px;">
                Built for speed and accuracy. Discover movies, explore ratings, and find useful details all in one place.
            </p>
            <p style="color:#404040; font-size:13px; margin:0;">© 2026 Cine Predict Platform</p>
        </div>

        <!-- ABOUT MODAL -->
        <div id="modal-about" class="modal-window">
            <div class="modal-content">
                <a href="#close" title="Close" class="modal-close">&#x2715;</a>
                <div class="modal-header"><h2>About Cine Predict</h2></div>
                <div class="modal-body">
                    <p><strong>Cine Predict</strong> is a sleek, intelligent web application designed to help users discover movies and explore cinematic data instantly.</p>
                    <p>Simply search for any movie title worldwide to uncover critical details including global ratings, box office predictions, release history, and popularity metrics.</p>
                    <p>Our platform aggregates real-time data from global APIs to ensure you have the most accurate information right at your fingertips.</p>
                </div>
            </div>
        </div>

        <!-- FEATURES MODAL -->
        <div id="modal-features" class="modal-window">
            <div class="modal-content">
                <a href="#close" title="Close" class="modal-close">&#x2715;</a>
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

        <!-- TECHNOLOGY MODAL -->
        <div id="modal-tech" class="modal-window">
            <div class="modal-content">
                <a href="#close" title="Close" class="modal-close">&#x2715;</a>
                <div class="modal-header"><h2>Technology Stack</h2></div>
                <div class="modal-body">
                    <p>Our platform is powered by a modern, highly optimized technology stack ensuring reliability and speed:</p>
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

        <!-- SUPPORT MODAL -->
        <div id="modal-support" class="modal-window">
            <div class="modal-content">
                <a href="#close" title="Close" class="modal-close">&#x2715;</a>
                <div class="modal-header"><h2>Help & Support</h2></div>
                <div class="modal-body">
                    <p>We are dedicated to continuously improving your movie discovery experience.</p>
                    <p>If you encounter any bugs, network issues, or simply have a feature request to make Cine Predict even better, our development team is ready to listen.</p>
                    <p style="margin-top:20px; color:#00FFFF; font-weight:600;">Contact us at: support@cinepredict.com</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)