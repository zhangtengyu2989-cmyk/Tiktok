"""
抖音真实数据采集器 v3
使用Playwright采集：热搜标题 + 搜索结果封面 + 视频评论
策略：
  - 标题从热搜获取
  - 封面从搜索结果页面提取
  - 评论从视频页面获取
  - 入库后每100条或每5分钟同步xlsx
"""
import os, re, sys, time, random, logging
from datetime import datetime
from typing import Optional, List, Dict

sys.stdout.reconfigure(encoding="utf-8")

logger = logging.getLogger("tiktokrx.crawler.real_collector")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

DB_PATH = "data/tiktok_baseline.db"
COOKIE_STR = os.environ.get(
    "DOUYIN_COOKIE",
    "passport_csrf_token=0532a50bb1d09ba9c932d4a41fc00bde; passport_csrf_token_default=0532a50bb1d09ba9c932d4a41fc00bde; enter_pc_once=1; UIFID_TEMP=355cad6f7c70d250eeaa616d7509b8b5280202d703b93e680c95fdfa3c8c225f22d831920283fc641b2d3f62f7a8439a57831cd01ae6541cb1d2e4032f6bd4f9079780ade2dd23022f5b8d347c23d56e; is_support_rtm_web_ts=1; hevc_supported=true; bd_ticket_guard_client_web_domain=2; is_staff_user=false; has_biz_token=false; __security_server_data_status=1; UIFID=355cad6f7c70d250eeaa616d7509b8b5280202d703b93e680c95fdfa3c8c225f22d831920283fc641b2d3f62f7a8439aa7e7da1d412de965da2a6dd2f7e30796d0722ba5fac1d8cd3cbc1d330c5c318415750ce3333ae7d607c0b77c294910fddb5a265d920a835075de3899a3518699abc0979d915a07e1e3c8fc6d807a1272ad2c107ef88595a7b5047d2aa06ed5802d59609c0fe4bcc6d49f4bb7af7a8d2c; my_rd=2; is_dash_user=1; publish_badge_show_info=%221%2C0%2C0%2C1777863357345%22; JXEntranceNegative=1; stream_player_status_params=%22%7B%5C%22is_auto_play%5C%22%3A0%2C%5C%22is_full_screen%5C%22%3A0%2C%5C%22is_full_webscreen%5C%22%3A0%2C%5C%22is_mute%5C%22%3A0%2C%5C%22is_speed%5C%22%3A1%2C%5C%22is_visible%5C%22%3A0%7D%22; download_guide=%223%2F20260505%2F0%22; strategyABtestKey=%221778030171.226%22; passport_mfa_token=CjV56dKPydl9xmef1SlB0xgf1vopU7u%2FRMbOxwYmlmfDA7i7kpor%2FSAi4q1EC%2BpRxyk5y%2BAjTRpKCjwAAAAAAAAAAAAAUGI4smP9XelEiVPca9yyrBUZDpj%2FV%2BLag8O35j6HrSAZA%2B8wtQYDFV%2Fus5fkZD2qTdgQ1NmQDhj2sdFsIAIiAQOFMuAm; d_ticket=66664a6b6556d6ef46d1c2fdc16538c91ebeb; passport_assist_user=Cj0qMzDL0mcucVqmoZcT7K-hwROTl0xi1sg8lyDTfTGOX0DT_pkb8i_um-fcFpjTfdpwOtnZo1aEe3p8u1C6GkoKPAAAAAAAAAAAAABQYs2V-AW-rx2lex_SC3M2LMcrVolMe0Mh56Cc0xRyUJsdXF-oP4BMxinYS9_86RIcERDd2JAOGImv1lQgASIBA0q2xI0%3D; n_mh=91mVQip5jBE5K7w0o5PhuDG-qkl2wG4xqoEdABWsknU; sid_guard=e07ec2a20b03594b25215990460d112f%7C1778030206%7C5184000%7CSun%2C+05-Jul-2026+01%3A16%3A46+GMT; uid_tt=c66160a02175ed3cde9c5495b0d367e8; uid_tt_ss=c66160a02175ed3cde9c5495b0d367e8; sid_tt=e07ec2a20b03594b25215990460d112f; sessionid=e07ec2a20b03594b25215990460d112f; sessionid_ss=e07ec2a20b03594b25215990460d112f; session_tlb_tag=sttt%7C18%7C4H7CogsDWUslIVmQRg0RL__________3iAWzZz0fdJjTqLfz_wmU-jHmR5PXuDEzRPDDA5yxjuw%3D; sid_ucp_v1=1.0.0-KDZlNGMzNWFiMDc3YTI3YTE1ZjViYzQ5ODBkM2MwMjYwYTZjNjNlMjkKHwiZqt7b9AIQ_qzqzwYY7zEgDDDj2PLYBTgFQPsHSAQaAmxxIiBlMDdlYzJhMjBiMDM1OTRiMjUyMTU5OTA0NjBkMTEyZg; ssid_ucp_v1=1.0.0-KDZlNGMzNWFiMDc3YTI3YTE1ZjViYzQ5ODBkM2MwMjYwYTZjNjNlMjkKHwiZqt7b9AIQ_qzqzwYY7zEgDDDj2PLYBTgFQPsHSAQaAmxxIiBlMDdlYzJhMjBiMDM1OTRiMjUyMTU5OTA0NjBkMTEyZg; login_time=1778030206707; _bd_ticket_crypt_cookie=df476afefcbbc0c61f80c5d6b9d04905; ttwid=1%7C4X1b9cU9HSf7Mo_6na1bdZEycApjXhvzcDAX1dAR0UQ%7C1778030208%7Cfa9931f644c78fee7b37c1579fffe327341a4802235c8caad82cadda36cea076; FOLLOW_NUMBER_YELLOW_POINT_INFO=%22MS4wLjABAAAAOiTM9HLtVopBEwAhUIBP8fFzhnpw9SHckeNSb1YMG_U%2F1778083200000%2F0%2F1778030284061%2F0%22; SelfTabRedDotControl=%5B%7B%22id%22%3A%227481129626580813864%22%2C%22u%22%3A195%2C%22c%22%3A0%7D%2C%7B%22id%22%3A%227547781036176836654%22%2C%22u%22%3A103%2C%22c%22%3A0%7D%2C%7B%22id%22%3A%227561409728040716342%22%2C%22u%22%3A17%2C%22c%22%3A0%7D%2C%7B%22id%22%3A%227601869536752584704%22%2C%22u%22%3A38%2C%22c%22%3A0%7D%2C%7B%22id%22%3A%227417741176792418343%22%2C%22u%22%3A151%2C%22c%22%3A0%7D%2C%7B%22id%22%3A%227149888940684609575%22%2C%22u%22%3A84%2C%22c%22%3A0%7D%2C%7B%22id%22%3A%227561386345344534580%22%2C%22u%22%3A9%2C%22c%22%3A0%7D%2C%7B%22id%22%3A%227078877517548881957%22%2C%22u%22%3A149%2C%22c%22%3A0%7D%2C%7B%22id%22%3A%227127938451522029605%22%2C%22u%22%3A35%2C%22c%22%3A0%7D%5D; volume_info=%7B%22isUserMute%22%3Afalse%2C%22isMute%22%3Atrue%2C%22volume%22%3A0.5%7D; __security_mc_1_s_sdk_crypt_sdk=ea74d1f7-4818-8b27; __security_mc_1_s_sdk_cert_key=8dc634f4-4413-b175; __security_mc_1_s_sdk_sign_data_key_web_protect=616d1dc7-4130-8f5c; stream_recommend_feed_params=%22%7B%5C%22cookie_enabled%5C%22%3Atrue%2C%5C%22screen_width%5C%22%3A1440%2C%5C%22screen_height%5C%22%3A900%2C%5C%22browser_online%5C%22%3Atrue%2C%5C%22cpu_core_num%5C%22%3A16%2C%5C%22device_memory%5C%22%3A8%2C%5C%22downlink%5C%22%3A6.1%2C%5C%22effective_type%5C%22%3A%5C%224g%5C%22%2C%5C%22round_trip_time%5C%22%3A100%7D%22; FOLLOW_LIVE_POINT_INFO=%22MS4wLjABAAAAOiTM9HLtVopBEwAhUIBP8fFzhnpw9SHckeNSb1YMG_U%2F1778083200000%2F0%2F1778031675644%2F0%22; bd_ticket_guard_client_data=eyJiZC10aWNrZXQtZ3VhcmQtdmVyc2lvbiI6MiwiYmQtdGlja2V0LWd1YXJkLWl0ZXJhdGlvbi12ZXJzaW9uIjoxLCJiZC10aWNrZXQtZ3VhcmQtcmVlLXB1YmxpYy1rZXkiOiJCQjQydmF6NnNlZEFjQWMyQWp1SWpDYjc3cjBtY1BXSmpPNnFIdGNmQ1lpWGI2K2xYWXZTSnFUNGpqTTdDRHY4Uk4vMXZvbExXcXErcE1HQXlCRnJENDg9IiwiYmQtdGlja2V0LWd1YXJkLXdlYi12ZXJzaW9uIjoyfQ%3D%3D; home_can_add_dy_2_desktop=%221%22; odin_tt=b739d450055aa36d5f22c26360282b75327111c7dcfad8338ed373b7748cbca0039d88fe80854a740b142411a7e1029ae0a30bdd32006455cda36838a0a1a773a6302256386c5798844b5ecb0101457f; biz_trace_id=683694d5; IsDouyinActive=true; sdk_source_info=7e276470716a68645a606960273f276364697660272927676c715a6d6069756077273f276364697660272927666d776a68605a607d71606b766c6a6b5a7666776c7571273f275e58272927666a6b766a69605a696c6061273f27636469766027292762696a6764695a7364776c6467696076273f275e582729277672715a646971273f2763646976602729277f6b5a666475273f2763646976602729276d6a6e5a6b6a716c273f2763646976602729276c6b6f5a7f6367273f27636469766027292771273f273131323c32363036353d323234272927676c715a75776a716a666a69273f2763646976602778; bit_env=eWcbVcBPDB3M6KYF10BftqhTRYABg6FeYF3xumDkt7sLcf_Q2_s8bQCK8XNKeZUvLBhdTLg4qQg-2kcSdMksvn7_dvIFUem4mWlc7Obv63tmKJGFk40kM1Aj4pKjg16v28dt2rMY4BMSnxU6GbR4DDpxrHy4_NerAyOxqFP-oDSY5miaYpMWCc1istDenzMdIcZ9VJkyKyEjRzb1CXuxjumllkr2CEOUQK8M4iRnzkZjsFXA62gj5JsuuJIWrSF7P9NmXVz4cY0UpTMSOZzrEX8n4MyFaxrsLVSO-az9shQ0jl833ITyndBV9LdFxiHx9SnnawugzHxqqmw25FmCY-rK2EM8O6hSEgRN6eVs_AHop4ctO-AziyGEGsfUlZ8F9GtX3_bB5qkhCa92KZ-7q9r7Yfts4zqkidvMu5PT2NeLw0Oo-Ir9uZ1YT_I1Tn_JCW2DuuYLIIkxRM0fxb0lUahB9PS6OqaJnChvsBPL86iU39tPkW-SfyyY7c_-VjFM1Lb2bHU2bgCblLnFclnV2loHRm_VW7pe3qQBLVOg1iA%3D; gulu_source_res=eyJwX2luIjoiNWU4NzE4YTdkYjIxMWYwYmQ1ODQ5MzQzZjM4ZGIyMDA1YjMwY2M2OGQ2Y2VjMWQzYmExYWU3ZTVjNTBlOWZlYSJ9; passport_auth_mix_state=8zwuv2m7regh5or4c9qwr6qccug1h2o9; bd_ticket_guard_client_data_v2=eyJyZWVfcHVibGljX2tleSI6IkJCNDJ2YXo2c2VkQWNBYzJBanVJakNiNzdyMG1jUFdKak82cUh0Y2ZDWWlYYjYrbFhZdlNKcVQ0ampNN0NEdjhSTi8xdm9sTFdxcStwTUdBeUJGckQ0OD0iLCJ0c19zaWduIjoidHMuMi5hYThlZTMyMjVlYjViNzg5NWIyOWE1M2YxNGFiNDhkMDJhMDYxOTVmMDNlZDI0ZDhhMGIzM2RlMWFlMjgxNTY5YzRmYmU4N2QyMzE5Y2YwNTMxODYyNGNlZGExNDkxMWNhNDA2ZGVkYmViZWRkYjJlMzBmY2U4ZDRmYTAyNTc1ZCIsInJlcV9jb250ZW50Ijoic2VjX3RzIiwicmVxX3NpZ24iOiIrSERDWHU3RnlRYkJOcGlSOEd3Wi9mdkxHamhvSFJBMjZBdDVKQ1RBaVpZPSIsInNlY190cyI6IiNhTWZ6VEdFd1hxWWdjOXNqMGRuY2QrM2xLWER5V29WbW9tWGQwb2FycFRRQ0dURGJNWmExMmo5R3JobGMifQ%3D%3D"
)

def parse_cookies(cookie_str: str) -> List[Dict]:
    cookies = []
    for item in cookie_str.split(';'):
        item = item.strip()
        if '=' in item:
            name, value = item.split('=', 1)
            cookies.append({'name': name.strip(), 'value': value.strip(), 'domain': '.douyin.com', 'path': '/'})
    return cookies

# ============ 数据库 ============
def get_db_count(table: str) -> int:
    import sqlite3
    try:
        conn = sqlite3.connect(DB_PATH)
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        conn.close()
        return count
    except:
        return 0

def init_tables():
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS title_database (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, hot_value INTEGER DEFAULT 0,
        category TEXT, label TEXT, source TEXT DEFAULT '', has_number INTEGER DEFAULT 0,
        has_exclaim INTEGER DEFAULT 0, has_emoji INTEGER DEFAULT 0, has_question INTEGER DEFAULT 0,
        has_suspense INTEGER DEFAULT 0, emotion_words INTEGER DEFAULT 0, title_length INTEGER DEFAULT 0,
        crawled_at TEXT, UNIQUE(title, source))""")
    conn.execute("""CREATE TABLE IF NOT EXISTS cover_database (
        id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT, video_id TEXT, color_tone TEXT DEFAULT '',
        avg_color TEXT DEFAULT '', hue REAL DEFAULT 0, saturation REAL DEFAULT 0, lightness REAL DEFAULT 0,
        composition_type TEXT DEFAULT '', text_overlay_detected INTEGER DEFAULT 0,
        face_detected INTEGER DEFAULT 0, source TEXT DEFAULT '', category TEXT, analyzed_at TEXT,
        UNIQUE(url, source))""")
    conn.execute("""CREATE TABLE IF NOT EXISTS comment_database (
        id INTEGER PRIMARY KEY AUTOINCREMENT, text TEXT NOT NULL, like_count INTEGER DEFAULT 0,
        comment_type TEXT DEFAULT 'general_type', sentiment TEXT DEFAULT 'neutral',
        user_nickname TEXT DEFAULT '', user_region TEXT DEFAULT '', aweme_id TEXT DEFAULT '',
        category TEXT, source TEXT DEFAULT '', crawled_at TEXT,
        UNIQUE(text, source, aweme_id))""")
    conn.execute("""CREATE TABLE IF NOT EXISTS bgm_database (
        id INTEGER PRIMARY KEY AUTOINCREMENT, song_name TEXT NOT NULL, artist TEXT DEFAULT '',
        bgm_name TEXT NOT NULL, style TEXT DEFAULT '动感', categories TEXT DEFAULT '',
        heat_index INTEGER DEFAULT 0, heat_level TEXT DEFAULT 'C', source TEXT DEFAULT '',
        douyin_matched INTEGER DEFAULT 0, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(bgm_name, source))""")
    conn.execute("""CREATE TABLE IF NOT EXISTS video_database (
        id INTEGER PRIMARY KEY AUTOINCREMENT, aweme_id TEXT UNIQUE, title TEXT, desc TEXT,
        cover_url TEXT, music_id TEXT, music_title TEXT, music_author TEXT, music_duration INTEGER,
        category TEXT, view_count INTEGER, like_count INTEGER, comment_count INTEGER,
        share_count INTEGER, create_time INTEGER, author TEXT, source TEXT DEFAULT 'unknown',
        crawled_at TEXT)""")
    conn.commit()
    conn.close()

# ============ xlsx 同步 ============
_sync_count = 0
_last_sync_time = time.time()

def trigger_sync():
    global _sync_count, _last_sync_time
    now = time.time()
    if _sync_count >= 100:
        logger.info(f"[xlsx] 达到条数阈值({_sync_count}条)，触发同步")
        do_sync(); _sync_count = 0; _last_sync_time = time.time()
    elif now - _last_sync_time >= 300:
        logger.info(f"[xlsx] 达到时间阈值({int(now-_last_sync_time)}秒)，触发同步")
        do_sync(); _sync_count = 0; _last_sync_time = time.time()

def do_sync():
    try:
        from .xlsx_sync import sync_all_tables_to_xlsx
        db_dir = os.path.dirname(os.path.abspath(DB_PATH))
        result = sync_all_tables_to_xlsx(DB_PATH, os.path.join(db_dir, "抖音原始数据"))
        if result: logger.info(f"[xlsx] 同步成功: {result}")
    except Exception as e:
        logger.warning(f"[xlsx] 同步失败: {e}")

def on_record_saved():
    global _sync_count
    _sync_count += 1
    trigger_sync()

# ============ 工具函数 ============
CATEGORY_KEYWORDS = {
    "food": ["美食","吃播","探店","烹饪","菜谱","厨房","减肥","外卖","烘焙","小吃","家常菜","甜品","饮品"],
    "fashion": ["穿搭","美妆","护肤","发型","衣服","裙子","裤子","搭配","化妆品","口红","香水","医美"],
    "tech": ["手机","电脑","数码","测评","科技","软件","教程","iPhone","安卓","显卡","耳机","相机","无人机"],
    "travel": ["旅行","旅游","攻略","打卡","景点","酒店","机票","出国","签证","自驾","露营","海岛"],
    "lifestyle": ["生活","日常","vlog","情感","解压","收纳","清洁","自律","理财","职场","人际","心理","健康"],
}

def infer_category(text: str) -> str:
    text_lower = text.lower()
    scores = {cat: sum(1 for kw in kws if kw.lower() in text_lower) for cat, kws in CATEGORY_KEYWORDS.items()}
    return max(scores, key=scores.get) if max(scores.values()) > 0 else "other"

def extract_hook_info(title: str) -> dict:
    return {
        "has_number": 1 if re.search(r'\d', title) else 0,
        "has_exclaim": 1 if re.search(r'[！？!]', title) else 0,
        "has_emoji": 1 if re.search(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF✨🔥]', title) else 0,
        "has_question": 1 if re.search(r'[？？?]', title) else 0,
        "has_suspense": 1 if any(w in title for w in ["竟然","没想到","原来","真相","揭秘","背后","原因","终于","其实","但是"]) else 0,
        "emotion_words": sum(1 for w in ["绝了","太牛了","哭了","救命","宝藏","神仙","炸裂","封神","无敌","逆天"] if w in title),
        "length": len(title),
    }

# ============ 保存函数 ============
def save_title(title: str, hot_value: int, source: str) -> bool:
    import sqlite3
    from datetime import datetime
    category = infer_category(title)
    hook = extract_hook_info(title)
    now = datetime.now().isoformat()
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""INSERT OR IGNORE INTO title_database
            (title, hot_value, category, source, has_number, has_exclaim, has_emoji,
             has_question, has_suspense, emotion_words, title_length, crawled_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (title, hot_value, category, source, hook["has_number"], hook["has_exclaim"],
             hook["has_emoji"], hook["has_question"], hook["has_suspense"],
             hook["emotion_words"], hook["length"], now))
        conn.commit(); conn.close()
        on_record_saved(); return True
    except: return False

def save_cover(url: str, video_id: str, category: str, source: str) -> bool:
    import sqlite3
    from datetime import datetime
    from .cover_analyzer import full_cover_analysis
    try:
        # 下载封面图并进行完整视觉分析
        analysis = full_cover_analysis(url)
        if analysis is None:
            # 分析失败时也保存一条记录，仅记录 URL 等基本信息
            analysis = {"url": url, "color_tone": "", "avg_color": "", "hue": 0,
                        "saturation": 0, "lightness": 0, "composition_type": "",
                        "text_overlay_detected": 0, "face_detected": 0,
                        "analyzed_at": datetime.now().isoformat()}
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""INSERT OR IGNORE INTO cover_database
            (url, video_id, color_tone, avg_color, hue, saturation, lightness,
             composition_type, text_overlay_detected, face_detected,
             category, source, analyzed_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (url, video_id, analysis.get("color_tone", ""), analysis.get("avg_color", ""),
             analysis.get("hue", 0), analysis.get("saturation", 0), analysis.get("lightness", 0),
             analysis.get("composition_type", ""), analysis.get("text_overlay_detected", 0),
             analysis.get("face_detected", 0), category, source, analysis.get("analyzed_at", "")))
        conn.commit(); conn.close()
        on_record_saved(); return True
    except Exception as e:
        logger.warning(f"封面保存失败 {url}: {e}")
        return False

def save_comment(text: str, aweme_id: str, category: str, source: str, video_title: str = "") -> bool:
    import sqlite3
    from datetime import datetime
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""INSERT OR IGNORE INTO comment_database
            (text, aweme_id, category, source, crawled_at, video_title)
            VALUES (?,?,?,?,?,?)""",
            (text, aweme_id, category, source, datetime.now().isoformat(), video_title[:100]))
        conn.commit(); conn.close()
        on_record_saved(); return True
    except: return False

# ============ Playwright 采集 ============
def fetch_douyin_hot_search(limit: int = 50) -> list:
    import httpx
    try:
        resp = httpx.get(
            "https://www.douyin.com/aweme/v1/web/hot/search/list/",
            params={"device_platform": "android", "aid": "6383", "version_name": "23.5.0"},
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "Cookie": COOKIE_STR, "Referer": "https://www.douyin.com/"},
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            word_list = data.get("data", {}).get("word_list", []) or []
            results = []
            for item in word_list[:limit]:
                word = item.get("word", "").strip()
                if word:
                    results.append({"title": word, "hot_value": item.get("hot_value", 0), "label": item.get("label", "")})
            logger.info(f"[API] 抖音热搜获取 {len(results)} 条")
            return results
    except Exception as e:
        logger.warning(f"[API] 抖音热搜失败: {e}")
    return []

def pw_search_and_extract(keyword: str, cookies: List[Dict]) -> List[Dict]:
    """用Playwright搜索关键词，返回视频信息列表"""
    from playwright.sync_api import sync_playwright
    videos = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            context.add_cookies(cookies)
            page = context.new_page()

            # 搜索页面
            search_url = f"https://www.douyin.com/search/{keyword}?type=video"
            page.goto(search_url, timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            # 滚动加载
            for _ in range(3):
                page.evaluate("window.scrollBy(0, 800)")
                page.wait_for_timeout(1000)

            # 提取视频信息
            html = page.content()

            # 找视频ID和封面
            video_pattern = r'/video/(\d+)'
            cover_pattern = r'(https?://[^\s"\'<>]+(?:p\d\.douyinpic\.com|douyinvod\.com)[^\s"\'<>]+)'
            video_ids = re.findall(video_pattern, html)
            covers = re.findall(cover_pattern, html)

            # 去重
            seen = set()
            unique_ids = []
            for vid in video_ids:
                if vid not in seen and len(vid) > 10:
                    seen.add(vid)
                    unique_ids.append(vid)

            seen_urls = set()
            unique_covers = []
            for url in covers:
                if url not in seen_urls and 'watermark' not in url:
                    seen_urls.add(url)
                    unique_covers.append(url)

            for i, vid in enumerate(unique_ids[:10]):
                videos.append({
                    "aweme_id": vid,
                    "cover_url": unique_covers[i] if i < len(unique_covers) else "",
                    "title": keyword,
                })

            browser.close()
    except Exception as e:
        logger.warning(f"[PW] 搜索 '{keyword}' 失败: {e}")
    return videos

def pw_get_comments(aweme_id: str, cookies: List[Dict], max_comments: int = 20) -> List[Dict]:
    """用Playwright获取视频评论"""
    from playwright.sync_api import sync_playwright
    comments = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            context.add_cookies(cookies)
            page = context.new_page()

            page.goto(f"https://www.douyin.com/video/{aweme_id}", timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(4000)

            # 滚动加载评论
            for _ in range(5):
                page.evaluate("window.scrollBy(0, 500)")
                page.wait_for_timeout(800)
            page.evaluate("window.scrollBy(0, -200)")
            page.wait_for_timeout(500)

            # 提取评论
            selectors = ['[data-e2e="comment-list"] li', '.comment-item', '[class*="comment"] li']
            for sel in selectors:
                items = page.query_selector_all(sel)
                if items:
                    for item in items[:max_comments]:
                        try:
                            # 评论内容
                            text_els = item.query_selector_all('span, [class*="text"], [class*="content"]')
                            text = ""
                            for te in text_els:
                                t = te.inner_text().strip()
                                if len(t) > 5 and '作者赞过' not in t and '回复' not in t[:3]:
                                    text = t
                                    break
                            if text and len(text) > 3:
                                # 点赞数
                                like_els = item.query_selector_all('[class*="like"], [class*="count"]')
                                likes = 0
                                for le in like_els:
                                    lt = le.inner_text().strip()
                                    if lt.isdigit():
                                        likes = int(lt)
                                        break
                                # 用户名
                                name_el = item.query_selector('[class*="name"], [class*="nickname"]')
                                nickname = name_el.inner_text().strip() if name_el else "匿名用户"

                                # IP属地
                                ip_el = item.query_selector('[class*="ip"], [class*="region"]')
                                ip_region = ip_el.inner_text().strip() if ip_el else ""

                                comments.append({
                                    "text": text[:200],
                                    "like_count": likes,
                                    "user_nickname": nickname[:30],
                                    "user_region": ip_region,
                                })
                        except:
                            pass
                    break

            browser.close()
    except Exception as e:
        logger.warning(f"[PW] 获取评论 {aweme_id} 失败: {e}")
    return comments[:max_comments]

# ============ 主流程 ============
def crawl_real_data(target_titles: int = 500, target_covers: int = 500):
    init_tables()
    cookies = parse_cookies(COOKIE_STR)

    logger.info("=" * 50)
    logger.info("抖音真实数据采集 v3 (Playwright)")
    logger.info(f"目标: 标题≥{target_titles}, 封面≥{target_covers}")
    logger.info("=" * 50)
    logger.info(f"当前: title={get_db_count('title_database')}, cover={get_db_count('cover_database')}, comment={get_db_count('comment_database')}")

    # Step 1: 获取热搜标题
    hot_items = fetch_douyin_hot_search(100)
    if not hot_items:
        logger.error("[ERROR] 无法获取热搜，请检查Cookie")
        return

    logger.info(f"获取到 {len(hot_items)} 条热搜")

    # Step 2: 处理每个热搜
    for i, item in enumerate(hot_items):
        keyword = item.get("title", "").strip()
        hot_value = item.get("hot_value", 0)
        if not keyword or len(keyword) < 3:
            continue

        logger.info(f"[{i+1}/{len(hot_items)}] 关键词: {keyword[:30]}...")

        # 保存标题
        save_title(keyword, hot_value, "douyin_hot")

        # 用Playwright搜索获取视频封面
        videos = pw_search_and_extract(keyword, cookies)
        if videos:
            logger.info(f"  找到 {len(videos)} 个视频")
            for v in videos[:5]:  # 每个关键词最多5个视频
                aweme_id = v["aweme_id"]
                category = infer_category(keyword)

                # 保存封面
                if v.get("cover_url"):
                    save_cover(v["cover_url"], aweme_id, category, "douyin_search")

                # 获取评论
                comments = pw_get_comments(aweme_id, cookies, max_comments=10)
                for c in comments:
                    save_comment(c["text"], aweme_id, category, "douyin_pw", keyword)
                logger.info(f"  视频 {aweme_id[:15]}... 评论{len(comments)}条")
        else:
            logger.info(f"  无视频结果")

        # 防封延迟
        time.sleep(random.uniform(2.0, 4.0))

        # 进度报告
        if (i + 1) % 5 == 0:
            logger.info(f"--- 进度 {i+1}/{len(hot_items)} ---")
            logger.info(f"  标题: {get_db_count('title_database')}, 封面: {get_db_count('cover_database')}, 评论: {get_db_count('comment_database')}")

        # 达到目标提前停止
        if get_db_count('title_database') >= target_titles and get_db_count('cover_database') >= target_covers:
            logger.info(f"已达到目标，停止采集")
            break

    # 最终统计和同步
    logger.info("\n" + "=" * 50)
    logger.info("采集完成，最终统计:")
    for t in ["title_database", "cover_database", "comment_database", "bgm_database", "video_database"]:
        logger.info(f"  {t}: {get_db_count(t)}")
    logger.info("=" * 50)

    logger.info("\n执行最终xlsx同步...")
    do_sync()
    logger.info("采集完成!")


if __name__ == "__main__":
    crawl_real_data(target_titles=500, target_covers=500)
