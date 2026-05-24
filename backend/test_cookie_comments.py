"""
测试登录态Cookie获取评论 - 滚动加载更多
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import re
from playwright.sync_api import sync_playwright

TEST_AWEME_ID = '7604384176132934938'

USER_COOKIES = '''passport_csrf_token=0532a50bb1d09ba9c932d4a41fc00bde; passport_csrf_token_default=0532a50bb1d09ba9c932d4a41fc00bde; enter_pc_once=1; UIFID_TEMP=355cad6f7c70d250eeaa616d7509b8b5280202d703b93e680c95fdfa3c8c225f22d831920283fc641b2d3f62f7a8439a57831cd01ae6541cb1d2e4032f6bd4f9079780ade2dd23022f5b8d347c23d56e; is_support_rtm_web_ts=1; hevc_supported=true; bd_ticket_guard_client_web_domain=2; is_staff_user=false; has_biz_token=false; __security_server_data_status=1; UIFID=355cad6f7c70d250eeaa616d7509b8b5280202d703b93e680c95fdfa3c8c225f22d831920283fc641b2d3f62f7a8439aa7e7da1d412de965da2a6dd2f7e30796d0722ba5fac1d8cd3cbc1d330c5c318415750ce3333ae7d607c0b77c294910fddb5a265d920a835075de3899a3518699abc0979d915a07e1e3c8fc6d807a1272ad2c107ef88595a7b5047d2aa06ed5802d59609c0fe4bcc6d49f4bb7af7a8d2c; my_rd=2; is_dash_user=1; publish_badge_show_info=%221%2C0%2C0%2C1777863357345%22; volume_info=%7B%22isUserMute%22%3Afalse%2C%22isMute%22%3Afalse%2C%22volume%22%3A0.5%7D; strategyABtestKey=%221777913688.549%22; FOLLOW_NUMBER_YELLOW_POINT_INFO=%22MS4wLjABAAAAOiTM9HLtVopBEwAhUIBP8fFzhnpw9SHckeNSb1YMG_U%2F1777996800000%2C0%2C1777913792277%2F0%22; gulu_source_res=eyJwX2luIjoiNWU4NzE4YTdkYjIxMWYwYmQ1ODQ5MzQzZjM4ZGIyMDA1YjMwY2M2OGQ2Y2VjMWQzYmExYWU3ZTVjNTBlOWZlYSJ9; FOLLOW_LIVE_POINT_INFO=%22MS4wLjABAAAAOiTM9HLtVopBEwAhUIBP8fFzhnpw9SHckeNSb1YMG_U%2F1777996800000%2C0%2C1777914589576%2F0%22; stream_recommend_feed_params=%22%7B%5C%22cookie_enabled%5C%22%3Atrue%2C%5C%22screen_width%5C%22%3A1440%2C%5C%22screen_height%5C%22%3A900%2C%5C%22browser_online%5C%22%3Atrue%2C%5C%22cpu_core_num%5C%22%3A16%2C%5C%22device_memory%5C%22%3A8%2C%5C%22downlink%5C%22%3A6.1%2C%5C%22effective_type%5C%22%3A%5C%224g%5C%22%2C%5C%22round_trip_time%5C%22%3A150%7D%22; passport_assist_user=CkFByGYlnJ3B2TNSrdNs4PI3Ta83svkIX-IQrhfv5tYx09rxm7zWM6dkV6FquDexwQp8iuhDPIY5Ime9VV-AKIwXbBpKCjwAAAAAAAAAAAAAUGEz9tNt-lGUllpnGVnIGIDmArXjQrckfybyThoa8Kx2Zq3JQcWOdQPEbj5i15D4dc8Q38iQDhiJr9ZUIAEiAQMmZgq-; n_mh=66RTXutGTbApSOOKr8NYvbDARXzNK-zko655cUK8fE0; sid_guard=f7c00ec12d797e524c7daf204089f90f%7C1777914636%7C5184000%7CFri%2C+03-Jul-2026+17%3A10%3A36+GMT; uid_tt=4c5bcd0257b35d18f8a66b5aabec39a8; uid_tt_ss=4c5bcd0257b35d18f8a66b5aabec39a8; sid_tt=f7c00ec12d797e524c7daf204089f90f; sessionid=f7c00ec12d797e524c7daf204089f90f; sessionid_ss=f7c00ec12d797e524c7daf204089f90f; session_tlb_tag=sttt%7C4%7C98AOwS15flJMfa8gQIn5D_________-y1Q7uVBfYDvbHbT6DZgJts0niB4iFV7uh6UoRWB4bLXs%3D; sid_ucp_v1=1.0.0-KDRmYWNiYThmYzY4MGVjNzZiMzZiMTNiM2M5MGIyZDQ3MGViYjExMjQKIQjQs-DK9a3QBRCMpuPPBhjvMSAMMLqq1scGOAdA9AdIBBoCbHEiIGY3YzAwZWMxMmQ3OTdlNTI0YzdkYWYyMDQwODlmOTBm; ssid_ucp_v1=1.0.0-KDRmYWNiYThmYzY4MGVjNzZiMzZiMTNiM2M5MGIyZDQ3MGViYjExMjQKIQjQs-DK9a3QBRCMpuPPBhjvMSAMMLqq1scGOAdA9AdIBBoCbHEiIGY3YzAwZWMxMmQ3OTdlNTI0YzdkYWYyMDQwODlmOTBm; _bd_ticket_crypt_cookie=fd825ed28c9624d6b309eb106e4a61cf; __security_mc_1_s_sdk_sign_data_key_web_protect=71c59b31-4fbc-953c; __security_mc_1_s_sdk_cert_key=e3456b23-4ece-8315; __security_mc_1_s_sdk_crypt_sdk=99c74d2d-4f4f-b043; login_time=1777914635737; IsDouyinActive=true; bd_ticket_guard_client_data=eyJiZC10aWNrZXQtZ3VhcmQtdmVyc2lvbiI6MiwiYmQtdGlja2V0LWd1YXJkLWl0ZXJhdGlvbi12ZXJzaW9uIjoxLCJiZC10aWNrZXQtZ3VhcmQtcmVlLXB1YmxpYy1rZXkiOiJCQjQydmF6NnNlZEFjQWMyQWp1SWpDYjc3cjBtY1BXSmpPNnFIdGNmQ1lpWGI2K2xYWXZTSnFUNGpqTTdDRHY4Uk4vMXZvbExXcXErcE1HQXlCRnJENDg9IiwiYmQtdGlja2V0LWd1YXJkLXdlYi12ZXJzaW9uIjoyfQ%3D%3D; home_can_add_dy_2_desktop=%221%22; ttwid=1%7C4X1b9cU9HSf7Mo_6na1bdZEycApjXhvzcDAX1dAR0UQ%7C1777914640%7Cc541fa7f577e8c4be2d7e1f3074c1321465bfbc0c0ac0c04cb64c00a1dd05e2b; sdk_source_info=7e276470716a68645a606960273f276364697660272927676c715a6d6069756077273f276364697660272927666d776a68605a607d71606b766c6a6b5a7666776c7571273f275e58272927666a6b766a69605a696c6061273f27636469766027292762696a6764695a7364776c6467696076273f275e582729277672715a646971273f2763646976602729277f6b5a666475273f2763646976602729276d6a6e5a6b6a716c273f2763646976602729276c6b6f5a7f6367273f27636469766027292771273f27323c3735313331343c32323234272927676c715a75776a716a666a69273f2763646976602778; bit_env=UPhhIALrAFRkn6TgYUwRRwvs2VVbXqTVkGGAuBlQ3VMVTeG9P4Y9rm4gxAUuSQf3LymWIg4tXoKBuXNAcZzG-qEiU2eX3j9cxDNDs3FDHxVxJkFqoLgfaKpIrLLuzM7ugzPwAkQkZaZBMVyOJxcfmjRL1puZ0daAQQiSPUAyWrILEA1uvh_L_5YxxylFlFunmJzoO1O6EW0w7XbBoGbednL_R2CJpDckU_qCRxJ2Tdd4Nbb7kKiIimC57T2JHSpUDXnRDRyWtQ_w1S1wtYYijnRSMlFK6XIqZFNqYjK1KBWHeSGKvtS-2Erc6c6TtjLhoXYVyCvUckcAwiC79VGTm5GYct3Jg-sXLBi67qMxqfdxTRkZ9M9zx-TNTK-t7XtCLXKKWPJJP36ARYyOLLtFh9II4VIxoOd8KRpKCjnJktLX23cS9mpdJ-w3kEjQ2WwCXetyeYgj6Wrd5RnMdE7_oHSoVAcA6FQkOVDcUXvt5cJ_chOMb3TJ_CZ0NZmlIMV4rQ-axOyitoLpjavJoZ7d2W8c9rAXh5i1eqr51_RMkuM%3D; passport_auth_mix_state=n7swx0ir55gz5e046hpi2bvgerl81vb8; odin_tt=d520c676bf3d814a6a317047f2b895173201cb4564206c42876100b44642ca2e69e99508731542d9947eb2c2afd571e807b3564d6cd0643b32d7c84b090cf2b0cf0ec35f87ac84054341b4627988184b; biz_trace_id=bf00ddf9; bd_ticket_guard_client_data_v2=eyJyZWVfcHVibGljX2tleSI6IkJCNDJ2YXo2c2VkQWNBYzJBanVJakNiNzdyMG1jUFdKak82cUh0Y2ZDWWlYYjYrbFhZdlNKcVQ0ampNN0NEdjhSTi8xdm9sTFdxcStwTUdBeUJGckQ0OD0iLCJ0c19zaWduIjoidHMuMi45YzlhMjAxNzY4M2YxZmY3NjNiNjE1NDkzNTg2ZjIzNzA2ZDJiMTU1ZDM4MzJkZDk2YmYzYWYxNTA3YWFjODhmYzRmYmU4N2QyMzE5Y2YwNTMxODYyNGNlZGExNDkxMWNhNDA2ZGVkYmViZWRkYjJlMzBmY2U4ZDRmYTAyNTc1ZCIsInJlcV9jb250ZW50Ijoic2VjX3RzIiwicmVxX3NpZ24iOiJmOTQ3Zk5tdkFXSG5JbGtpZkIvYVFwVjlCQi9mVDNHWERvU01GUkQ2Q2NrPSIsInNlY190cyI6IiNlY3ZMY2FTYjNLcjdXVDE2ODR1VkxhaTR4Sjl2RGRGNUxrNnl4MEtGZURnaWpVWnlkVVpsUlBzR2NXUGoifQ%3D%3D; download_guide=%222%2F20260505%2F0%22; JXEntranceNegative=1; SelfTabRedDotControl=%5B%5D; stream_player_status_params=%22%7B%5C%22is_auto_play%5C%22%3A0%2C%5C%22is_full_screen%5C%22%3A0%2C%5C%22is_full_webscreen%5C%22%3A0%2C%5C%22is_mute%5C%22%3A0%2C%5C%22is_speed%5C%22%3A1%2C%5C%22is_visible%5C%22%3A1%7D%22'''

def test_logged_in_comments_with_scroll():
    print(f'测试视频: {TEST_AWEME_ID}')
    print('使用登录态Cookie + 滚动加载获取评论...')

    # 解析Cookie
    cookie_list = []
    for cookie in USER_COOKIES.split('; '):
        if '=' in cookie:
            name, value = cookie.split('=', 1)
            cookie_list.append({
                'name': name.strip(),
                'value': value.strip(),
                'domain': '.douyin.com',
                'path': '/'
            })

    print(f'解析到 {len(cookie_list)} 个Cookie')

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 720}
        )

        context.add_cookies(cookie_list)
        page = context.new_page()

        print('访问视频页面...')
        page.goto(f'https://www.douyin.com/video/{TEST_AWEME_ID}', timeout=30000, wait_until='domcontentloaded')

        # 等待初始加载
        page.wait_for_timeout(5000)

        # 滚动评论区域多次加载更多
        print('滚动评论区域加载更多...')
        for i in range(5):
            page.evaluate('window.scrollBy(0, 500)')
            page.wait_for_timeout(1500)
            page.evaluate('window.scrollBy(0, -200)')
            page.wait_for_timeout(1000)

        # 提取评论
        all_comments = []
        try:
            comment_list = page.query_selector('[data-e2e="comment-list"]')
            if comment_list:
                print('找到评论列表')
                html = comment_list.inner_html()
                pattern = r'>([^<]{5,200})<'
                matches = re.findall(pattern, html)

                for m in matches:
                    text = m.strip()
                    if len(text) > 3 and not text.startswith('@') and ':' not in text[:10]:
                        if not any(kw in text for kw in ['分享', '回复', '互相关', '作者赞过', 'http']):
                            if not re.match(r'^\d+[万分]?$', text):
                                if not re.search(r'\d+小时|\d+分钟|\d+天|\d+周|\d+月', text):
                                    all_comments.append(text[:200])

            # 去重
            seen = set()
            unique = []
            for c in all_comments:
                if c not in seen and len(c) > 5:
                    seen.add(c)
                    unique.append(c)

            all_comments = unique[:50]

        except Exception as e:
            print(f'提取评论失败: {e}')

        print(f'\n获取到 {len(all_comments)} 条评论:')
        for i, c in enumerate(all_comments):
            print(f'  {i+1}. {c[:60]}...' if len(c) > 60 else f'  {i+1}. {c}')

        browser.close()

    return len(all_comments)

if __name__ == '__main__':
    count = test_logged_in_comments_with_scroll()
    print(f'\n测试完成，共获取 {count} 条评论')
