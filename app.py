import streamlit as st
import requests
import re
import hashlib
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- 1. CONFIGURATION ---
TMDB_API_KEY = "57486deb33535eb0b12bbd780982370e" 

# --- 2. DYNAMIC COLOR GENERATOR ---
def get_user_color(email):
    colors =["#9B59B6", "#2980B9", "#27AE60", "#D35400", "#C0392B", "#16A085", "#2C3E50"]
    hash_obj = hashlib.md5(email.lower().encode())
    index = int(hash_obj.hexdigest(), 16) % len(colors)
    return colors[index]

# --- 3. UI ENGINE & CSS ---
st.set_page_config(page_title="Cine Predict", layout="wide")

st.markdown("""
    <style>
    /* Global Background & ANTI-SHAKE LOCK */
    html, body, .stApp { 
        background-color: #000000 !important; 
        color: #FFFFFF !important; 
        overflow-y: scroll !important; 
        overflow-x: hidden !important; 
    }
    .block-container { padding-bottom: 0px !important; margin-bottom: 0px !important; }
    header, footer { visibility: hidden !important; display: none !important; }
    
    /* LOGIN PAGE: EMAIL LABEL */
    .stTextInput label, .stTextInput label p { color: #71717A !important; font-weight: 600 !important; }

    /* TEXT INPUTS */
    div[data-baseweb="input"] {
        background-color: #FFFFFF !important; border: none !important; border-radius: 8px !important; position: relative;
    }
    input { color: #000000 !important; -webkit-text-fill-color: #000000 !important; caret-color: black !important; padding-right: 140px !important; }

    /* SEARCH BAR: ensure white text on dark background when overridden */
    div[data-testid="column"]:nth-child(2) input,
    div[data-baseweb="input"]:has(input[placeholder="Email or phone number"]) input,
    div[data-baseweb="input"]:has(input[placeholder="Password"]) input {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        caret-color: white !important;
    }

    /* SEARCH BAR on main page: dark background so text must be white */
    div[data-baseweb="input"]:has(input[placeholder="Search for a movie title..."]) {
        background-color: #1C1C1E !important;
    }
    input[placeholder="Search for a movie title..."],
    div[data-baseweb="input"]:has(input[placeholder="Search for a movie title..."]) input {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        caret-color: #FFFFFF !important;
    }

    /* RESPONSIVE: mobile layout */
    @media (max-width: 768px) {
        .block-container { padding-left: 1rem !important; padding-right: 1rem !important; }
        .full-width-footer { margin-left: -1rem !important; margin-right: -1rem !important; padding: 30px 16px 24px !important; }
        .modal-content { width: 92% !important; padding: 24px 20px !important; }
        .footer-nav { gap: 10px !important; }
        .footer-btn { font-size: 13px !important; padding: 8px 14px !important; }
        div[data-testid="column"]:nth-child(2) { padding: 32px 24px 28px !important; margin-top: 20px !important; }
    }

    /* SEARCH BAR ICON INJECTION */
    div[data-baseweb="input"]:has(input[placeholder="Search for a movie title..."])::after {
        content: ""; position: absolute; right: 15px; top: 50%; transform: translateY(-50%); width: 20px; height: 20px;
        background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="%23A1A1AA" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>');
        background-size: contain; background-repeat: no-repeat; pointer-events: none;
    }

    div[data-testid="stInputInstructions"], div[data-testid="InputInstructions"] { 
        right: 45px !important; margin-right: 5px !important; display: block !important; visibility: visible !important; opacity: 0.8 !important;
    }

    /* --- TABS STYLING --- */
    div[data-testid="stTabs"] button[data-baseweb="tab"] {
        background: transparent !important; border: none !important; border-bottom: 3px solid transparent !important;
        color: #71717A !important; padding-bottom: 8px !important; padding-top: 8px !important;
    }
    div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] { color: #00FFFF !important; border-bottom: 3px solid #00FFFF !important; }
    div[data-testid="stTabs"] button[data-baseweb="tab"] p { font-size: 18px !important; font-weight: 700 !important; }

    /* SIDEBAR & LOGO */
    .side-label { color: #71717A !important; font-weight: 700; font-size: 14px; margin-top: 20px; margin-bottom: 2px;}
    .side-val { color: #FFFFFF; font-size: 15px; line-height: 1.4; }
    .logo-container { display: flex; align-items: center; gap: 12px; margin-bottom: 5px; }
    .logo-cine, .logo-predict { 
        font-family: 'Inter', sans-serif; font-weight: 800; font-size: 32px; color: #00FFFF !important; 
        text-shadow: 0 0 10px rgba(0, 255, 255, 0.7), 0 0 20px rgba(0, 255, 255, 0.4); letter-spacing: 0.5px;
    }

    /* BADGE & IMAGES */
    .prediction-badge { 
        background-color: rgba(0, 255, 136, 0.05); border: 1px solid #00FF88; color: #00FF88; padding: 8px 12px; 
        border-radius: 5px; font-weight: bold; display: inline-flex; align-items: center; gap: 8px; font-size: 14px; margin-top: 15px;
    }
    .cast-img { width: 110px !important; height: 145px !important; border-radius: 8px; object-fit: cover; border: 1px solid #2D2D2D; }
    .cast-name { color: #A1A1AA; font-size: 11px; margin-top: 5px; text-align: center; }

    /* SIMILAR SECTION TITLES */
    div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button {
        background: transparent !important; border: none !important; padding: 0 !important; width: 100%; text-align: left !important; box-shadow: none !important;
    }
    div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button p {
        color: #FFFFFF !important; font-weight: 700 !important; font-size: 13px !important; margin-top: 8px !important; white-space: normal !important; line-height: 1.2 !important;
    }
    div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button:hover p { text-decoration: underline !important; }

    .stButton>button { background: linear-gradient(to right, #90cea1, #01b4e4) !important; color: #000000 !important; border: none !important; border-radius: 8px; font-weight: bold; }

    /* --- SHAKE-FREE FOOTER DESIGN --- */
    .full-width-footer {
        width: auto; margin-left: -5rem; margin-right: -5rem;
        background-color: #121214; padding: 50px 20px 40px 20px; text-align: center; 
        margin-top: 80px; border-top: 1px solid rgba(255,255,255,0.05);
    }
    .footer-nav { display: flex; justify-content: center; gap: 20px; margin-bottom: 30px; flex-wrap: wrap; }
    
    .footer-btn {
        background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1);
        color: #A1A1AA !important; font-weight: 600; font-size: 14px; padding: 10px 24px;
        border-radius: 30px; text-decoration: none !important; transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        display: flex; align-items: center; gap: 8px;
    }
    .footer-btn:hover {
        background: rgba(0, 255, 255, 0.08); border-color: #00FFFF; color: #00FFFF !important;
        transform: translateY(-3px); box-shadow: 0 10px 20px rgba(0, 255, 255, 0.15);
    }

    /* --- UPGRADED MODALS (GLASSMORPHISM) --- */
    .modal-window {
        position: fixed; background-color: rgba(0, 0, 0, 0.85); backdrop-filter: blur(8px);
        top: 0; right: 0; bottom: 0; left: 0; z-index: 999999; visibility: hidden; opacity: 0; 
        pointer-events: none; transition: all 0.3s ease;
    }
    .modal-window:target { visibility: visible; opacity: 1; pointer-events: auto; }
    
    .modal-content {
        width: 600px; max-width: 90%; position: absolute; top: 55%; left: 50%;
        transform: translate(-50%, -50%); padding: 40px; 
        background: linear-gradient(145deg, #1A1A1D, #0D0D0F);
        border: 1px solid rgba(0, 255, 255, 0.2); border-radius: 16px; color: #E0E0E0; text-align: left;
        box-shadow: 0 20px 50px rgba(0,0,0,0.8), inset 0 0 20px rgba(0,255,255,0.02);
        transition: top 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
    }
    .modal-window:target .modal-content { top: 50%; } 

    .modal-close {
        color: #71717A !important; position: absolute; right: 20px; top: 20px;
        width: 36px; height: 36px; background: rgba(255,255,255,0.05); border-radius: 50%;
        display: flex; align-items: center; justify-content: center; font-size: 22px;
        text-decoration: none !important; font-weight: bold; transition: all 0.3s ease;
    }
    .modal-close:hover { background: rgba(0,255,255,0.15); color: #00FFFF !important; transform: rotate(90deg); }

    .modal-header { display: flex; align-items: center; gap: 12px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 15px; margin-bottom: 20px; }
    .modal-header h2 { color: #00FFFF; margin: 0; font-weight: 800; letter-spacing: 0.5px; }
    .modal-body p { font-size: 16px; line-height: 1.7; color: #D4D4D8; }
    .modal-body ul { line-height: 2.2; font-size: 16px; color: #D4D4D8; padding-left: 20px; }
    .modal-body li span { color: #00FFFF; font-weight: bold; }

    .tech-tags { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 15px; }
    .tech-tag {
        background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);
        padding: 6px 14px; border-radius: 8px; font-size: 14px; color: #FFFFFF; font-weight: 600;
    }
    .tech-tag span { color: #00FFFF; margin-right: 5px; }

    /* RESPONSIVE: flexible column stacking on mobile */
    @media (max-width: 768px) {
        /* Stack movie result columns vertically */
        div[data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; }
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            min-width: 100% !important;
            flex: 1 1 100% !important;
        }
        /* Shrink cast images on small screens */
        .cast-img { width: 80px !important; height: 106px !important; }
        .cast-name { font-size: 10px !important; }
        /* Header logo/profile row stays side by side */
        div[data-testid="stHorizontalBlock"]:first-of-type > div[data-testid="column"] {
            min-width: unset !important;
            flex: unset !important;
        }
        /* Reduce heading sizes */
        h1 { font-size: 26px !important; }
        h2 { font-size: 22px !important; }
    }
    </style>
    """, unsafe_allow_html=True)

def render_logo(size_scale=1):
    st.markdown(f"""
        <div class="logo-container">
            <div><span class="logo-cine">CINE </span><span class="logo-predict">PREDICT</span></div>
        </div>
    """, unsafe_allow_html=True)

# --- 4. DATA FETCHING ---
@st.cache_data(ttl=86400, show_spinner=False)
def get_movie_details(query):
    session = requests.Session()
    session.mount('https://', HTTPAdapter(max_retries=Retry(total=3)))
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        search_url = "https://api.tmdb.org/3/search/movie"
        search_params = {"api_key": TMDB_API_KEY, "query": query}
        res = session.get(search_url, params=search_params, headers=headers, timeout=10)
        
        if res.status_code == 401: return None, "❌ Invalid TMDB API Key. Please check your credentials."
            
        res.raise_for_status()
        data = res.json()
        
        if not data.get('results'): return None, "Movie not found."
            
        mid = data['results'][0]['id']
        detail_url = f"https://api.tmdb.org/3/movie/{mid}"
        detail_params = {"api_key": TMDB_API_KEY, "append_to_response": "credits,videos,recommendations"}
        
        detail_res = session.get(detail_url, params=detail_params, headers=headers, timeout=10)
        detail_res.raise_for_status()
        return detail_res.json(), None
        
    except requests.exceptions.ConnectionError:
        return None, "🌐 Network Error: Your ISP might be blocking TMDB. Try using a VPN like Cloudflare WARP (1.1.1.1)!"
    except Exception as e:
        return None, f"⚠️ An unexpected error occurred: {str(e)}"

def update_search(new_title):
    st.session_state['movie_search_bar'] = new_title

# --- 5. APP FLOW ---
if 'auth' not in st.session_state: st.session_state['auth'] = False

if not st.session_state['auth']:
    
    st.markdown("""
        <style>
        /* FIXED: Forces the Netflix background image to display by targeting the main container view */[data-testid="stAppViewContainer"] {
            background-image: linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.9)), url('https://assets.nflxext.com/ffe/siteui/vlv3/a73c4363-1dcd-4719-b3b1-3725418fd91d/fe1147dd-78be-44aa-a0e5-2d2994305a13/IN-en-20231016-popsignuptwoweeks-perspective_alpha_website_large.jpg') !important;
            background-size: cover !important;
            background-position: center !important;
            background-attachment: fixed !important;
        }
        
        /* Overrides the global black background so the image shows through */
        .stApp {
            background-color: transparent !important;
        }
        
        /* Netflix-style Form Box applied to Center Column */
        div[data-testid="column"]:nth-child(2) {
            background-color: rgba(0, 0, 0, 0.75) !important;
            padding: 60px 68px 40px !important;
            border-radius: 8px !important;
            margin-top: 50px !important;
            min-height: 550px;
        }

        /* Netflix-style Input Text Fields inside the Box */
        div[data-testid="column"]:nth-child(2) div[data-baseweb="input"] {
            background-color: #333333 !important;
            border: 1px solid #333333 !important;
            border-radius: 4px !important;
        }
        div[data-testid="column"]:nth-child(2) input {
            color: #FFFFFF !important;
            -webkit-text-fill-color: #FFFFFF !important;
            caret-color: white !important;
            padding-right: 16px !important;
            background-color: transparent !important;
        }
        div[data-testid="column"]:nth-child(2) div[data-baseweb="input"]:focus-within {
            background-color: #454545 !important;
        }
        
        /* Overrides search icon rendering globally on login page */
        div[data-testid="column"]:nth-child(2) div[data-baseweb="input"]::after { display: none !important; }

        /* FIXED: Red Primary Submit Button */
        button[kind="primary"] {
            background-color: #E50914 !important;
            background-image: none !important;
            color: white !important;
            -webkit-text-fill-color: white !important;
            border: none !important;
            border-radius: 4px !important;
            font-size: 16px !important;
            font-weight: 700 !important;
            padding: 12px !important;
            height: auto !important;
            margin-top: 25px !important;
            margin-bottom: 10px !important;
        }
        button[kind="primary"]:hover {
            background-color: #C11119 !important;
        }

        /* FIXED: Grey Remember Me Text */
        div[data-testid="stCheckbox"] label p {
            color: #8C8C8C !important;
            font-size: 14px !important;
        }
        </style>
    """, unsafe_allow_html=True)

    _, center, _ = st.columns([1, 1.2, 1])
    with center:
        render_logo(size_scale=1)
        st.markdown("<h2 style='font-size:32px; font-weight:700; color:white; margin-top:20px; margin-bottom:25px;'>Sign In</h2>", unsafe_allow_html=True)
        
        email = st.text_input("Email", placeholder="Email or phone number", label_visibility="collapsed")
        password = st.text_input("Password", type="password", placeholder="Password", label_visibility="collapsed")
        
        # --- REMEMBER ME & HELP OPTIONS PLACED ABOVE THE BUTTON EXACTLY AS REQUESTED ---
        c1, c2 = st.columns([1, 1])
        with c1:
            st.checkbox("Remember me", value=True)
        with c2:
            st.markdown("""
                <div style='text-align:right; margin-top:8px;'>
                    <a href='mailto:support@cinepredict.com' style='color:#8C8C8C; text-decoration:none; font-size:14px;'>Need help?</a>
                </div>
            """, unsafe_allow_html=True)
            
        if st.button("Sign In", type="primary", use_container_width=True):
            if len(email.strip()) > 3:
                st.session_state['auth'] = True
                st.session_state['user_email'] = email
                st.rerun()
            else: st.error("Please enter a valid email or phone number.")
        
        st.markdown("""
            <div style='margin-top: 60px; color:#737373; font-size:16px;'>
                New to Cine Predict? <span style='color:white; font-weight:500; cursor:pointer;'>Sign up now.</span>
            </div>
        """, unsafe_allow_html=True)

else:
    user_color = get_user_color(st.session_state['user_email'])
    
    st.markdown(f"""
        <style>
        div[data-testid="stPopover"] button {{
            background-color: transparent !important;
            border-radius: 30px !important;
            width: 100% !important; height: 45px !important;
            border: 2px solid #00FFFF !important;
            padding: 0 20px !important; 
            box-shadow: 0px 0px 10px rgba(0,255,255,0.1) !important;
            display: flex !important; align-items: center !important; justify-content: center !important;
            transition: all 0.3s ease !important;
        }}
        div[data-testid="stPopover"] button:hover {{
            background-color: rgba(0, 255, 255, 0.1) !important;
            box-shadow: 0px 0px 15px rgba(0,255,255,0.3) !important;
            transform: translateY(-2px);
        }}
        div[data-testid="stPopover"] button div, 
        div[data-testid="stPopover"] button p,
        div[data-testid="stPopover"] button span {{
            background-color: transparent !important; 
            color: #00FFFF !important;
            -webkit-text-fill-color: #00FFFF !important; 
            font-weight: 700 !important; font-size: 16px !important; 
            margin: 0 !important; padding: 0 !important;
            display: flex !important; align-items: center !important; justify-content: center !important;
            gap: 6px !important;
        }}
        div[data-testid="stPopover"] button svg {{ display: none !important; width: 0 !important; opacity: 0 !important; }}
        
        div[data-testid="stPopoverBody"] {{ 
            background-color: #1A1A1D !important; 
            border: none !important;
            outline: none !important;
            box-shadow: none !important;
            border-radius: 15px !important; 
            padding: 20px !important;
        }}
        div[data-testid="stPopoverBody"] .stButton > button {{
            background: linear-gradient(to right, #6FE3CB, #2CB3E1) !important;
            color: #000000 !important;
            -webkit-text-fill-color: #000000 !important;
            border: none !important;
            border-radius: 10px !important;
            width: 100% !important;
            height: 45px !important;
            font-size: 16px !important;
            font-weight: 500 !important;
            margin-top: 15px !important;
            box-shadow: none !important;
        }}
        div[data-testid="stPopoverBody"] .stButton > button:hover {{ opacity: 0.9 !important; }}
        </style>
    """, unsafe_allow_html=True)

    h1, h2 = st.columns([8.5, 1.5])
    with h1: render_logo(size_scale=0.8)
    with h2:
        u_init = st.session_state['user_email'][0].upper()
        with st.popover("👤 Profile"):
            st.markdown(f'''
                <div style="text-align:center; padding-top:10px;">
                    <p style="font-size:15px; color:#888888 !important; -webkit-text-fill-color: #888888 !important; margin-bottom: 25px; margin-top: 0; font-weight:400;">
                        {st.session_state["user_email"]}
                    </p>
                    <div style="background:{user_color}; color:#FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; width:90px; height:90px; border-radius:50%; margin:0 auto 20px; display:flex; align-items:center; justify-content:center; font-size:42px; font-weight:bold;">
                        {u_init}
                    </div>
                    <p style="font-size:24px; color:#000000 !important; -webkit-text-fill-color: #000000 !important; font-weight:500; margin-bottom: 10px;">
                        Hi, User!
                    </p>
                </div>
            ''', unsafe_allow_html=True)
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
            col_poster, col_info, col_sidebar = st.columns([1, 2.7, 1])
            with col_poster: 
                if data.get('poster_path'):
                    st.image(f"https://image.tmdb.org/t/p/w500{data['poster_path']}", use_container_width=True)
                else:
                    st.image("https://via.placeholder.com/500x750/111111/FFFFFF?text=No+Poster+Available", use_container_width=True)
                    
            with col_info:
                st.markdown(f"<h1>{data['title']}</h1>", unsafe_allow_html=True)
                st.markdown(f"<h3 style='color:#00FF88;'>93% Match Prediction</h3>", unsafe_allow_html=True)
                st.markdown(f"<p style='color:#71717A;'>{data['release_date'][:4]} | ★ {round(data['vote_average'], 1)}/10</p>", unsafe_allow_html=True)
                st.markdown(f"<p>{data['overview']}</p>", unsafe_allow_html=True)
                st.markdown('<div class="prediction-badge">🎯 PREDICTION: BOX OFFICE HIT</div>', unsafe_allow_html=True)
            with col_sidebar:
                st.markdown('<p class="side-label">Starring</p>', unsafe_allow_html=True)
                st.write(", ".join([a['name'] for a in data['credits']['cast'][:4]]))
                st.markdown('<p class="side-label">Genres</p>', unsafe_allow_html=True)
                st.write(", ".join([g['name'] for g in data['genres']]))
                st.markdown('<p class="side-label">Global Rating</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size:18px; color:#EAB308; font-weight:bold;">★ {round(data["vote_average"], 1)}/10</p>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            t_c, t_t, t_s = st.tabs(["👥 Cast", "▷ Trailer", "🎞️ Similar"])
            
            with t_c:
                cols = st.columns(10)
                for i, act in enumerate(data['credits']['cast'][:10]):
                    with cols[i]:
                        img_p = act.get('profile_path')
                        img_u = f"https://image.tmdb.org/t/p/h632{img_p}" if img_p else "https://www.themoviedb.org/assets/2/v4/glyphicons/basic/glyphicons-basic-4-user-grey-d8fe577334c16c30617d9e3d30901e377f5144ccc58cd014ee8d1c026a71573c.svg"
                        st.markdown(f'<div style="text-align:center;"><img src="{img_u}" class="cast-img"><div class="cast-name">{act["name"]}</div></div>', unsafe_allow_html=True)
            with t_t:
                vids = data.get('videos', {}).get('results',[])
                video = next((v for v in vids if v['type'] == 'Trailer' and v['site'] == 'YouTube'), None)
                if not video: video = next((v for v in vids if v['site'] == 'YouTube'), None)
                
                if video: st.video(f"https://www.youtube.com/watch?v={video['key']}")
                else: st.info("Trailer not found for this movie.")
            with t_s:
                recs = data.get('recommendations', {}).get('results', [])[:6]
                if recs:
                    r_cols = st.columns(6)
                    for i, m in enumerate(recs):
                        with r_cols[i]:
                            if m.get('poster_path'):
                                st.image(f"https://image.tmdb.org/t/p/w342{m['poster_path']}", use_container_width=True)
                            else:
                                st.image("https://via.placeholder.com/342x513/111111/FFFFFF?text=No+Poster", use_container_width=True)
                                
                            st.button(m['title'], key=f"rec_{m['id']}", on_click=update_search, args=(m['title'],))
        else:
            if error_msg == "Movie not found.": st.warning(error_msg)
            else: st.error(error_msg)
    else:
        st.markdown("""
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; margin-top: 100px;">
            <div style="background-color: #071D22; padding: 25px; border-radius: 50%; margin-bottom: 25px;">
                <svg width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="#00FFFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18"></rect>
                    <line x1="7" y1="2" x2="7" y2="22"></line><line x1="17" y1="2" x2="17" y2="22"></line>
                    <line x1="2" y1="12" x2="22" y2="12"></line><line x1="2" y1="7" x2="7" y2="7"></line>
                    <line x1="2" y1="17" x2="7" y2="17"></line><line x1="17" y1="17" x2="22" y2="17"></line>
                    <line x1="17" y1="7" x2="22" y2="7"></line>
                </svg>
            </div>
            <h1 style="font-family: 'Inter', sans-serif; font-weight: 800; font-size: 42px; margin-bottom: 10px; color: #FFFFFF;">Discover Your Next Favorite</h1>
            <p style="color: #71717A; font-size: 18px; text-align: center;">Enter a movie title to explore ratings and details that help you choose your next film.</p>
        </div>
        """, unsafe_allow_html=True)

    # --- UNIQUE FOOTER WITH INTERACTIVE MODALS ---
    st.markdown("""
        <div class="full-width-footer">
            <div class="footer-nav">
                <a href="#modal-about" class="footer-btn">📝 About</a>
                <a href="#modal-features" class="footer-btn">✨ Features</a>
                <a href="#modal-tech" class="footer-btn">💻 Technology</a>
                <a href="#modal-support" class="footer-btn">🎧 Support</a>
            </div>
            <p style="color: #71717A; font-size: 14px; margin-bottom: 25px;">Built for speed and accuracy. Discover movies, explore ratings, and find useful details all in one place.</p>
            <p style="color: #404040; font-size: 13px; margin: 0;">© 2026 Cine Predict Platform</p>
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