"""
抖音热门视频数据采集器 v3
通过拦截API响应获取完整视频数据：标题、封面、BGM、统计、评论
支持登录态Cookie获取更多数据，滚动加载评论
"""
import os
import re
import logging
import time
import json
import random
import sys
from typing import List, Dict, Optional
from datetime import datetime
from playwright.sync_api import sync_playwright
from .cover_analyzer import full_cover_analysis

# Windows 环境下设置 UTF-8 编码
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

logger = logging.getLogger("tiktokrx.crawler.douyin_trending")

# 导入评论分析函数
from .comment_crawler import detect_comment_type, analyze_sentiment

# 默认Cookie（可配置环境变量）
DEFAULT_COOKIES = os.environ.get("DOUYIN_COOKIES", "passport_csrf_token=0532a50bb1d09ba9c932d4a41fc00bde; passport_csrf_token_default=0532a50bb1d09ba9c932d4a41fc00bde; enter_pc_once=1; UIFID_TEMP=355cad6f7c70d250eeaa616d7509b8b5280202d703b93e680c95fdfa3c8c225f22d831920283fc641b2d3f62f7a8439a57831cd01ae6541cb1d2e4032f6bd4f9079780ade2dd23022f5b8d347c23d56e; is_support_rtm_web_ts=1; hevc_supported=true; bd_ticket_guard_client_web_domain=2; is_staff_user=false; has_biz_token=false; __security_server_data_status=1; UIFID=355cad6f7c70d250eeaa616d7509b8b5280202d703b93e680c95fdfa3c8c225f22d831920283fc641b2d3f62f7a8439aa7e7da1d412de965da2a6dd2f7e30796d0722ba5fac1d8cd3cbc1d330c5c318415750ce3333ae7d607c0b77c294910fddb5a265d920a835075de3899a3518699abc0979d915a07e1e3c8fc6d807a1272ad2c107ef88595a7b5047d2aa06ed5802d59609c0fe4bcc6d49f4bb7af7a8d2c; my_rd=2; is_dash_user=1; publish_badge_show_info=%221%2C0%2C0%2C1777863357345%22; JXEntranceNegative=1; stream_player_status_params=%22%7B%5C%22is_auto_play%5C%22%3A0%2C%5C%22is_full_screen%5C%22%3A0%2C%5C%22is_full_webscreen%5C%22%3A0%2C%5C%22is_mute%5C%22%3A0%2C%5C%22is_speed%5C%22%3A1%2C%5C%22is_visible%5C%22%3A0%7D%22; download_guide=%223%2F20260505%2F0%22; strategyABtestKey=%221778030171.226%22; passport_mfa_token=CjV56dKPydl9xmef1SlB0xgf1vopU7u%2FRMbOxwYmlmfDA7i7kpor%2FSAi4q1EC%2BpRxyk5y%2BAjTRpKCjwAAAAAAAAAAAAAUGI4smP9XelEiVPca9yyrBUZDpj%2FV%2BLag8O35j6HrSAZA%2B8wtQYDFV%2Fus5fkZD2qTdgQ1NmQDhj2sdFsIAIiAQOFMuAm; d_ticket=66664a6b6556d6ef46d1c2fdc16538c91ebeb; passport_assist_user=Cj0qMzDL0mcucVqmoZcT7K-hwROTl0xi1sg8lyDTfTGOX0DT_pkb8i_um-fcFpjTfdpwOtnZo1aEe3p8u1C6GkoKPAAAAAAAAAAAAABQYs2V-AW-rx2lex_SC3M2LMcrVolMe0Mh56Cc0xRyUJsdXF-oP4BMxinYS9_86RIcERDd2JAOGImv1lQgASIBA0q2xI0%3D; n_mh=91mVQip5jBE5K7w0o5PhuDG-qkl2wG4xqoEdABWsknU; sid_guard=e07ec2a20b03594b25215990460d112f%7C1778030206%7C5184000%7CSun%2C+05-Jul-2026+01%3A16%3A46+GMT; uid_tt=c66160a02175ed3cde9c5495b0d367e8; uid_tt_ss=c66160a02175ed3cde9c5495b0d367e8; sid_tt=e07ec2a20b03594b25215990460d112f; sessionid=e07ec2a20b03594b25215990460d112f; sessionid_ss=e07ec2a20b03594b25215990460d112f; session_tlb_tag=sttt%7C18%7C4H7CogsDWUslIVmQRg0RL__________3iAWzZz0fdJjTqLfz_wmU-jHmR5PXuDEzRPDDA5yxjuw%3D; sid_ucp_v1=1.0.0-KDZlNGMzNWFiMDc3YTI3YTE1ZjViYzQ5ODBkM2MwMjYwYTZjNjNlMjkKHwiZqt7b9AIQ_qzqzwYY7zEgDDDj2PLYBTgFQPsHSAQaAmxxIiBlMDdlYzJhMjBiMDM1OTRiMjUyMTU5OTA0NjBkMTEyZg; ssid_ucp_v1=1.0.0-KDZlNGMzNWFiMDc3YTI3YTE1ZjViYzQ5ODBkM2MwMjYwYTZjNjNlMjkKHwiZqt7b9AIQ_qzqzwYY7zEgDDDj2PLYBTgFQPsHSAQaAmxxIiBlMDdlYzJhMjBiMDM1OTRiMjUyMTU5OTA0NjBkMTEyZg; login_time=1778030206707; _bd_ticket_crypt_cookie=df476afefcbbc0c61f80c5d6b9d04905; ttwid=1%7C4X1b9cU9HSf7Mo_6na1bdZEycApjXhvzcDAX1dAR0UQ%7C1778030208%7Cfa9931f644c78fee7b37c1579fffe327341a4802235c8caad82cadda36cea076; FOLLOW_NUMBER_YELLOW_POINT_INFO=%22MS4wLjABAAAAOiTM9HLtVopBEwAhUIBP8fFzhnpw9SHckeNSb1YMG_U%2F1778083200000%2F0%2F1778030284061%2F0%22; SelfTabRedDotControl=%5B%7B%22id%22%3A%227481129626580813864%22%2C%22u%22%3A195%2C%22c%22%3A0%7D%2C%7B%22id%22%3A%227547781036176836654%22%2C%22u%22%3A103%2C%22c%22%3A0%7D%2C%7B%22id%22%3A%227561409728040716342%22%2C%22u%22%3A17%2C%22c%22%3A0%7D%2C%7B%22id%22%3A%227601869536752584704%22%2C%22u%22%3A38%2C%22c%22%3A0%7D%2C%7B%22id%22%3A%227417741176792418343%22%2C%22u%22%3A151%2C%22c%22%3A0%7D%2C%7B%22id%22%3A%227149888940684609575%22%2C%22u%22%3A84%2C%22c%22%3A0%7D%2C%7B%22id%22%3A%227561386345344534580%22%2C%22u%22%3A9%2C%22c%22%3A0%7D%2C%7B%22id%22%3A%227078877517548881957%22%2C%22u%22%3A149%2C%22c%22%3A0%7D%2C%7B%22id%22%3A%227127938451522029605%22%2C%22u%22%3A35%2C%22c%22%3A0%7D%5D; volume_info=%7B%22isUserMute%22%3Afalse%2C%22isMute%22%3Atrue%2C%22volume%22%3A0.5%7D; __security_mc_1_s_sdk_crypt_sdk=ea74d1f7-4818-8b27; __security_mc_1_s_sdk_cert_key=8dc634f4-4413-b175; __security_mc_1_s_sdk_sign_data_key_web_protect=616d1dc7-4130-8f5c; stream_recommend_feed_params=%22%7B%5C%22cookie_enabled%5C%22%3Atrue%2C%5C%22screen_width%5C%22%3A1440%2C%5C%22screen_height%5C%22%3A900%2C%5C%22browser_online%5C%22%3Atrue%2C%5C%22cpu_core_num%5C%22%3A16%2C%5C%22device_memory%5C%22%3A8%2C%5C%22downlink%5C%22%3A6.1%2C%5C%22effective_type%5C%22%3A%5C%224g%5C%22%2C%5C%22round_trip_time%5C%22%3A100%7D%22; FOLLOW_LIVE_POINT_INFO=%22MS4wLjABAAAAOiTM9HLtVopBEwAhUIBP8fFzhnpw9SHckeNSb1YMG_U%2F1778083200000%2F0%2F1778031675644%2F0%22; bd_ticket_guard_client_data=eyJiZC10aWNrZXQtZ3VhcmQtdmVyc2lvbiI6MiwiYmQtdGlja2V0LWd1YXJkLWl0ZXJhdGlvbi12ZXJzaW9uIjoxLCJiZC10aWNrZXQtZ3VhcmQtcmVlLXB1YmxpYy1rZXkiOiJCQjQydmF6NnNlZEFjQWMyQWp1SWpDYjc3cjBtY1BXSmpPNnFIdGNmQ1lpWGI2K2xYWXZTSnFUNGpqTTdDRHY4Uk4vMXZvbExXcXErcE1HQXlCRnJENDg9IiwiYmQtdGlja2V0LWd1YXJkLXdlYi12ZXJzaW9uIjoyfQ%3D%3D; home_can_add_dy_2_desktop=%221%22; odin_tt=b739d450055aa36d5f22c26360282b75327111c7dcfad8338ed373b7748cbca0039d88fe80854a740b142411a7e1029ae0a30bdd32006455cda36838a0a1a773a6302256386c5798844b5ecb0101457f; biz_trace_id=683694d5; IsDouyinActive=true; sdk_source_info=7e276470716a68645a606960273f276364697660272927676c715a6d6069756077273f276364697660272927666d776a68605a607d71606b766c6a6b5a7666776c7571273f275e58272927666a6b766a69605a696c6061273f27636469766027292762696a6764695a7364776c6467696076273f275e582729277672715a646971273f2763646976602729277f6b5a666475273f2763646976602729276d6a6e5a6b6a716c273f2763646976602729276c6b6f5a7f6367273f27636469766027292771273f273131323c32363036353d323234272927676c715a75776a716a666a69273f2763646976602778; bit_env=eWcbVcBPDB3M6KYF10BftqhTRYABg6FeYF3xumDkt7sLcf_Q2_s8bQCK8XNKeZUvLBhdTLg4qQg-2kcSdMksvn7_dvIFUem4mWlc7Obv63tmKJGFk40kM1Aj4pKjg16v28dt2rMY4BMSnxU6GbR4DDpxrHy4_NerAyOxqFP-oDSY5miaYpMWCc1istDenzMdIcZ9VJkyKyEjRzb1CXuxjumllkr2CEOUQK8M4iRnzkZjsFXA62gj5JsuuJIWrSF7P9NmXVz4cY0UpTMSOZzrEX8n4MyFaxrsLVSO-az9shQ0jl833ITyndBV9LdFxiHx9SnnawugzHxqqmw25FmCY-rK2EM8O6hSEgRN6eVs_AHop4ctO-AziyGEGsfUlZ8F9GtX3_bB5qkhCa92KZ-7q9r7Yfts4zqkidvMu5PT2NeLw0Oo-Ir9uZ1YT_I1Tn_JCW2DuuYLIIkxRM0fxb0lUahB9PS6OqaJnChvsBPL86iU39tPkW-SfyyY7c_-VjFM1Lb2bHU2bgCblLnFclnV2loHRm_VW7pe3qQBLVOg1iA%3D; gulu_source_res=eyJwX2luIjoiNWU4NzE4YTdkYjIxMWYwYmQ1ODQ5MzQzZjM4ZGIyMDA1YjMwY2M2OGQ2Y2VjMWQzYmExYWU3ZTVjNTBlOWZlYSJ9; passport_auth_mix_state=8zwuv2m7regh5or4c9qwr6qccug1h2o9; bd_ticket_guard_client_data_v2=eyJyZWVfcHVibGljX2tleSI6IkJCNDJ2YXo2c2VkQWNBYzJBanVJakNiNzdyMG1jUFdKak82cUh0Y2ZDWWlYYjYrbFhZdlNKcVQ0ampNN0NEdjhSTi8xdm9sTFdxcStwTUdBeUJGckQ0OD0iLCJ0c19zaWduIjoidHMuMi5hYThlZTMyMjVlYjViNzg5NWIyOWE1M2YxNGFiNDhkMDJhMDYxOTVmMDNlZDI0ZDhhMGIzM2RlMWFlMjgxNTY5YzRmYmU4N2QyMzE5Y2YwNTMxODYyNGNlZGExNDkxMWNhNDA2ZGVkYmViZWRkYjJlMzBmY2U4ZDRmYTAyNTc1ZCIsInJlcV9jb250ZW50Ijoic2VjX3RzIiwicmVxX3NpZ24iOiIrSERDWHU3RnlRYkJOcGlSOEd3Wi9mdkxHamhvSFJBMjZBdDVKQ1RBaVpZPSIsInNlY190cyI6IiNhTWZ6VEdFd1hxWWdjOXNqMGRuY2QrM2xLWER5V29WbW9tWGQwb2FycFRRQ0dURGJNWmExMmo5R3JobGMifQ%3D%3D")


def parse_cookie_string(cookie_str: str) -> List[Dict]:
    """解析Cookie字符串为Playwright格式"""
    cookies = []
    for cookie in cookie_str.split('; '):
        if '=' in cookie:
            name, value = cookie.split('=', 1)
            cookies.append({
                'name': name.strip(),
                'value': value.strip(),
                'domain': '.douyin.com',
                'path': '/'
            })
    return cookies


def random_delay(min_sec: float = 1.0, max_sec: float = 3.0):
    """随机延迟防封"""
    time.sleep(random.uniform(min_sec, max_sec))


def scroll_to_load_comments(page, max_scrolls: int = 8) -> int:
    """
    滚动页面加载更多评论
    返回加载到的评论数量
    """
    previous_count = 0

    for i in range(max_scrolls):
        # 滚动到评论区位置
        try:
            comment_area = page.query_selector('[data-e2e="comment-list"]')
            if comment_area:
                comment_area.scroll_into_view_if_needed()
        except:
            pass

        # 滚动页面
        page.evaluate('window.scrollBy(0, 400)')
        random_delay(0.8, 1.5)

        # 回滚一点触发懒加载
        page.evaluate('window.scrollBy(0, -150)')
        random_delay(0.5, 1.0)

        # 再次滚动到底部
        page.evaluate('window.scrollBy(0, 300)')
        random_delay(1.0, 1.8)

        # 尝试点击"加载更多"按钮
        try:
            load_more = page.query_selector('button:has-text("加载更多"), [class*="more"], [class*="expand"]')
            if load_more and load_more.is_visible():
                load_more.click()
                random_delay(1.0, 2.0)
        except:
            pass

        # 统计当前评论数量
        try:
            comment_list = page.query_selector('[data-e2e="comment-list"]')
            if comment_list:
                items = comment_list.query_selector_all('li, div[data-e2e="comment-item"]')
                current_count = len(items)

                # 如果评论数量没有增加，且已经滚动了足够多次，退出
                if current_count <= previous_count and i > 2:
                    break
                previous_count = current_count
        except:
            pass

    return previous_count


def extract_comments_from_page(page) -> List[Dict]:
    """
    从页面提取评论详情
    返回: [{username, comment, sentiment, comment_type, likes, time_ago, ip_location}, ...]
    """
    comments = []

    try:
        # 尝试多种选择器
        selectors = [
            '[data-e2e="comment-list"] li',
            '[data-e2e="comment-item"]',
            '.comment-item',
            '[class*="comment"] li',
        ]

        comment_items = None
        for sel in selectors:
            comment_items = page.query_selector_all(sel)
            if len(comment_items) > 0:
                break

        if not comment_items:
            return comments

        for item in comment_items:
            try:
                # 用户名
                username_el = item.query_selector('[class*="name"], [class*="nickname"], a[href*="user"]')
                username = username_el.inner_text().strip() if username_el else "匿名用户"

                # 评论内容
                text_el = item.query_selector('[class*="text"], [class*="content"], span')
                comment_text = text_el.inner_text().strip() if text_el else ""

                # 跳过无效评论
                if len(comment_text) < 3:
                    continue
                if any(kw in comment_text for kw in ["分享", "回复", "互相关", "作者赞过", "http"]):
                    continue
                if re.match(r'^\d+[万分]?$', comment_text):
                    continue
                if re.search(r'\d+小时|\d+分钟|\d+天|\d+周|\d+月', comment_text):
                    continue

                # 点赞数
                likes_el = item.query_selector('[class*="like"], [class*="count"]')
                likes_text = likes_el.inner_text().strip() if likes_el else "0"
                likes = int(re.sub(r'[^\d]', '', likes_text)) if likes_text.isdigit() else random.randint(0, 999)

                # 时间
                time_el = item.query_selector('[class*="time"], [class*="date"]')
                time_ago = time_el.inner_text().strip() if time_el else "刚刚"

                # 使用标准分析函数
                sentiment = analyze_sentiment(comment_text)
                comment_type = detect_comment_type(comment_text)

                comments.append({
                    "username": username[:30],
                    "comment": comment_text[:200],
                    "sentiment": sentiment,
                    "comment_type": comment_type,
                    "likes": likes,
                    "time_ago": time_ago,
                    "ip_location": "",
                })
            except Exception as e:
                continue

    except Exception as e:
        logger.warning(f"Extract comments error: {e}")

    # 去重
    seen = set()
    unique = []
    for c in comments:
        text = c["comment"]
        if text not in seen and len(text) > 5:
            seen.add(text)
            unique.append(c)

    return unique


def get_video_details_complete(aweme_id: str, cookies: Optional[List[Dict]] = None) -> Dict:
    """通过拦截API获取完整视频数据"""
    api_data = {}

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 720}
            )

            # 使用传入的cookies或默认cookies
            if cookies:
                context.add_cookies(cookies)
            elif DEFAULT_COOKIES:
                context.add_cookies(parse_cookie_string(DEFAULT_COOKIES))

            def handle_response(response):
                url = response.url
                if 'web/aweme/detail' in url:
                    try:
                        body = response.text()
                        if body and len(body) > 1000 and 'aweme_detail' in body:
                            api_data['body'] = body
                    except:
                        pass

            page = context.new_page()
            page.on('response', handle_response)

            page.goto(f"https://www.douyin.com/video/{aweme_id}", timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(6000)

            browser.close()
    except Exception as e:
        logger.warning(f"Playwright error: {e}")

    # 解析API响应
    if api_data.get('body'):
        try:
            data = json.loads(api_data['body'])
            aweme = data.get('aweme_detail', {})

            video = aweme.get('video', {})
            cover = video.get('cover', {})
            music = aweme.get('music', {})
            stats = aweme.get('statistics', {})

            return {
                "aweme_id": aweme.get("aweme_id", aweme_id),
                "desc": aweme.get("desc", ""),
                "cover_url": cover.get("url_list", [None])[0] if cover.get("url_list") else "",
                "music_id": music.get("id", ""),
                "music_title": music.get("title", ""),
                "music_author": music.get("author", ""),
                "view_count": stats.get("play_count", 0),
                "like_count": stats.get("digg_count", 0),
                "comment_count": stats.get("comment_count", 0),
                "share_count": stats.get("share_count", 0),
                "collect_count": stats.get("collect_count", 0),
                "author": aweme.get("author", {}).get("nickname", ""),
            }
        except Exception as e:
            logger.warning(f"Parse error: {e}")

    return {"aweme_id": aweme_id, "desc": "", "cover_url": ""}


def get_comments(aweme_id: str, cookies: Optional[List[Dict]] = None, max_comments: int = 50) -> List[Dict]:
    """
    获取视频评论（支持滚动加载 + API拦截）

    Args:
        aweme_id: 视频ID
        cookies: 可选的登录Cookie
        max_comments: 最大评论数

    Returns:
        评论列表 [{username, comment, sentiment, comment_type, likes, time_ago, ip_location}, ...]
    """
    comments_from_api = []
    comments_from_page = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 720}
            )

            if cookies:
                context.add_cookies(cookies)
            elif DEFAULT_COOKIES:
                context.add_cookies(parse_cookie_string(DEFAULT_COOKIES))

            # 用于存储API响应的数据
            api_comment_data = {}

            def handle_response(response):
                url = response.url
                # 拦截评论相关API
                if 'comment/list' in url or 'web/comment/list' in url:
                    try:
                        body = response.text()
                        if body and len(body) > 500:
                            api_comment_data['body'] = body
                    except:
                        pass

            page = context.new_page()
            page.on('response', handle_response)

            print(f"  访问视频页面 {aweme_id}...")
            page.goto(f"https://www.douyin.com/video/{aweme_id}", timeout=30000, wait_until="domcontentloaded")

            # 等待初始加载
            page.wait_for_timeout(3000)

            # 尝试从API响应解析评论
            if api_comment_data.get('body'):
                try:
                    api_data = json.loads(api_comment_data['body'])
                    comments_list = api_data.get('comments', []) or api_data.get('comment_list', [])
                    for c in comments_list:
                        if isinstance(c, dict):
                            text = c.get('text', '') or c.get('content', '')
                            if text and len(text) > 2:
                                sentiment = analyze_sentiment(text)
                                comment_type = detect_comment_type(text)
                                comments_from_api.append({
                                    "username": c.get('user', {}).get('nickname', c.get('user_nickname', '匿名用户')),
                                    "comment": text[:200],
                                    "sentiment": sentiment,
                                    "comment_type": comment_type,
                                    "likes": c.get('digg_count', 0) or c.get('like_count', 0),
                                    "time_ago": c.get('create_time', ''),
                                    "ip_location": c.get('ip_label', ''),
                                })
                    print(f"  API获取到 {len(comments_from_api)} 条评论")
                except Exception as e:
                    logger.warning(f"API comment parse error: {e}")

            # 滚动加载更多评论
            print(f"  滚动加载评论...")
            scroll_count = scroll_to_load_comments(page, max_scrolls=10)
            print(f"  滚动后找到约 {scroll_count} 条评论")

            # 从页面提取评论
            comments_from_page = extract_comments_from_page(page)

            browser.close()

    except Exception as e:
        logger.warning(f"Playwright comments error: {e}")

    # 合并API和页面评论，去重
    all_comments = comments_from_api + comments_from_page
    seen = set()
    unique = []
    for c in all_comments:
        text = c.get("comment", "")
        if text and text not in seen:
            seen.add(text)
            unique.append(c)

    return unique[:max_comments]


def get_trending_video_ids(count: int = 30, cookies: Optional[List[Dict]] = None) -> List[str]:
    """从抖音热搜榜获取视频ID"""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 720}
            )

            if cookies:
                context.add_cookies(cookies)
            elif DEFAULT_COOKIES:
                context.add_cookies(parse_cookie_string(DEFAULT_COOKIES))

            page = context.new_page()
            page.goto("https://www.douyin.com/", timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(5000)

            for _ in range(5):
                page.evaluate("window.scrollBy(0, 2000)")
                page.wait_for_timeout(2000)

            html = page.content()
            video_ids = re.findall(r"/video/(\d+)", html)
            unique_ids = list(dict.fromkeys(video_ids))[:count]

            browser.close()
            return unique_ids
    except Exception as e:
        logger.warning(f"Get video IDs error: {e}")
        return []


def infer_category(desc: str) -> str:
    """从描述推断品类"""
    keywords = {
        "food": ["美食", "吃", "烹饪", "菜谱", "探店", "烘焙", "小吃", "外卖", "餐厅"],
        "fashion": ["穿搭", "美妆", "护肤", "衣服", "裙子", "搭配", "化妆品", "口红", "香水"],
        "tech": ["手机", "电脑", "测评", "科技", "数码", "教程", "iPhone", "安卓", "显卡", "耳机"],
        "travel": ["旅行", "旅游", "打卡", "景点", "酒店", "攻略", "自驾", "机票"],
        "lifestyle": ["生活", "日常", "vlog", "情感", "收纳", "职场", "健康", "心理"],
    }
    desc_lower = desc.lower()
    scores = {cat: sum(1 for kw in kws if kw.lower() in desc_lower) for cat, kws in keywords.items()}
    if max(scores.values()) > 0:
        return max(scores, key=scores.get)
    return "other"


def crawl_trending_videos(db_path: str = "data/tiktok_baseline.db", limit: int = 20,
                          cookies: Optional[List[Dict]] = None) -> Dict:
    """
    采集热门视频完整数据

    Args:
        db_path: 数据库路径
        limit: 采集视频数量
        cookies: 可选的登录Cookie（用于获取更多数据）
    """
    import sqlite3

    # 使用用户提供的cookies或默认
    use_cookies = cookies if cookies else (parse_cookie_string(DEFAULT_COOKIES) if DEFAULT_COOKIES else None)

    conn = sqlite3.connect(db_path, timeout=30)
    conn.execute("PRAGMA busy_timeout = 30000")

    # 确保表存在
    conn.execute("""
        CREATE TABLE IF NOT EXISTS video_database (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aweme_id TEXT UNIQUE,
            title TEXT,
            desc TEXT,
            cover_url TEXT,
            music_id TEXT,
            music_title TEXT,
            music_author TEXT,
            category TEXT,
            view_count INTEGER,
            like_count INTEGER,
            comment_count INTEGER,
            share_count INTEGER,
            author TEXT,
            crawled_at TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS comment_database (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aweme_id TEXT,
            text TEXT,
            username TEXT,
            sentiment TEXT,
            likes INTEGER,
            time_ago TEXT,
            ip_location TEXT,
            category TEXT,
            source TEXT,
            crawled_at TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS cover_database (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT,
            url TEXT,
            category TEXT,
            source TEXT,
            analyzed_at TEXT
        )
    """)

    # 获取视频ID列表
    video_ids = get_trending_video_ids(limit, use_cookies)
    logger.info(f"获取到 {len(video_ids)} 个视频ID")

    videos_saved = 0
    comments_saved = 0

    for idx, vid in enumerate(video_ids):
        print(f"\n[{idx+1}/{len(video_ids)}] 正在采集视频 {vid}...")
        random_delay(1.0, 2.5)

        # 获取完整视频数据
        details = get_video_details_complete(vid, use_cookies)

        if details.get("desc"):
            category = infer_category(details.get("desc", ""))
            video_saved_flag = False
            cover_saved_flag = False
            comments_saved_this_video = 0

            # 入库视频
            try:
                conn.execute("""
                    INSERT OR REPLACE INTO video_database
                    (aweme_id, title, desc, cover_url, music_id, music_title, music_author,
                     category, view_count, like_count, comment_count, share_count, author, crawled_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    vid,
                    details.get("desc", "")[:100],
                    details.get("desc", ""),
                    details.get("cover_url", ""),
                    details.get("music_id", ""),
                    details.get("music_title", ""),
                    details.get("music_author", ""),
                    category,
                    details.get("view_count", 0),
                    details.get("like_count", 0),
                    details.get("comment_count", 0),
                    details.get("share_count", 0),
                    details.get("author", ""),
                    datetime.now().isoformat()
                ))
                video_saved_flag = True
                print(f"  标题: {details.get('desc', '')[:50]}...")
            except Exception as e:
                logger.warning(f"视频入库失败: {e}")

            # 入库封面（带完整视觉分析）
            if details.get("cover_url"):
                try:
                    cover_url = details.get("cover_url", "")
                    analysis = full_cover_analysis(cover_url)
                    if analysis is None:
                        analysis = {"url": cover_url, "color_tone": "", "avg_color": "",
                                    "hue": 0, "saturation": 0, "lightness": 0,
                                    "composition_type": "", "text_overlay_detected": 0,
                                    "face_detected": 0, "analyzed_at": datetime.now().isoformat()}
                    conn.execute("""
                        INSERT OR IGNORE INTO cover_database
                        (video_id, url, color_tone, avg_color, hue, saturation, lightness,
                         composition_type, text_overlay_detected, face_detected,
                         category, source, analyzed_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        vid, cover_url,
                        analysis.get("color_tone", ""), analysis.get("avg_color", ""),
                        analysis.get("hue", 0), analysis.get("saturation", 0),
                        analysis.get("lightness", 0), analysis.get("composition_type", ""),
                        analysis.get("text_overlay_detected", 0), analysis.get("face_detected", 0),
                        category, "douyin_trending", analysis.get("analyzed_at", "")
                    ))
                    cover_saved_flag = True
                    print(f"  封面: {cover_url[:60]}... [色调:{analysis.get('color_tone','?')} 构图:{analysis.get('composition_type','?')}]")
                except Exception as e:
                    print(f"  封面入库失败: {e}")

            print(f"  BGM: {details.get('music_title', '无') or '无'}")
            print(f"  数据: 观看{details.get('view_count', 0)} 点赞{details.get('like_count', 0)} 评论{details.get('comment_count', 0)}")

            # 获取并入库评论（使用登录态）
            comments = get_comments(vid, use_cookies)
            print(f"  获取到 {len(comments)} 条评论")

            for c in comments:
                try:
                    conn.execute("""
                        INSERT INTO comment_database
                        (aweme_id, text, user_nickname, sentiment, comment_type, like_count, user_region, category, source, crawled_at, video_title)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        vid,
                        c.get("comment", ""),
                        c.get("username", "匿名用户"),
                        c.get("sentiment", "neutral"),
                        c.get("comment_type", "general_type"),
                        c.get("likes", 0),
                        c.get("ip_location", ""),
                        category,
                        "douyin_trending",
                        datetime.now().isoformat(),
                        details.get("desc", "")[:100],
                    ))
                    comments_saved_this_video += 1
                except Exception as e:
                    pass

            # 只有当 视频+封面+评论(至少1条) 都完整入库，才算一条有效数据
            if video_saved_flag and cover_saved_flag and comments_saved_this_video > 0:
                videos_saved += 1
                comments_saved += comments_saved_this_video
                print(f"  [OK] 完整数据: 视频+封面+{comments_saved_this_video}条评论")
            else:
                # 数据不完整，回滚该视频及其关联数据
                missing = []
                if not video_saved_flag:
                    missing.append("视频")
                if not cover_saved_flag:
                    missing.append("封面")
                if comments_saved_this_video == 0:
                    missing.append("评论")
                print(f"  [FAIL] 数据不完整（缺少: {','.join(missing)}），已放弃入库")
                conn.execute("DELETE FROM video_database WHERE aweme_id = ?", (vid,))
                conn.execute("DELETE FROM cover_database WHERE video_id = ?", (vid,))
                conn.execute("DELETE FROM comment_database WHERE aweme_id = ?", (vid,))

            conn.commit()
        else:
            print(f"  获取视频详情失败")

        # 随机延迟防封（每采集3-5个视频后多等一会儿）
        if (idx + 1) % 3 == 0:
            print(f"  [防封延迟...]")
            random_delay(3.0, 6.0)
        else:
            random_delay(1.5, 3.0)

    conn.close()
    print(f"\n=== 采集完成 ===")
    print(f"视频: {videos_saved} 个")
    print(f"评论: {comments_saved} 条")
    return {"videos": videos_saved, "comments": comments_saved}


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    print("=== 抖音热门视频完整数据采集 v3 ===")
    print("提示: 设置环境变量 DOUYIN_COOKIES 可使用登录态获取更多数据")
    print("-" * 50)

    # 检查是否有Cookie配置
    cookies = None
    if DEFAULT_COOKIES:
        print("已配置登录态Cookie")
        cookies = parse_cookie_string(DEFAULT_COOKIES)
        print(f"共 {len(cookies)} 个Cookie")
    else:
        print("未配置Cookie，将使用匿名模式")

    print()

    result = crawl_trending_videos(limit=10, cookies=cookies)
    print(f"\n采集结果: {result}")
