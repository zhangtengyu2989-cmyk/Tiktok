"""
封面图分析爬虫
从视频URL提取封面帧，分析视觉特征
注意：此模块主要做图像分析，原始封面帧需从视频提取
"""
import logging
import io
import re
from typing import Dict, List, Optional
from urllib.parse import urlparse

logger = logging.getLogger("tiktokrx.crawler.cover")

# 颜色HSL区间定义
COLOR_RANGES = {
    "bright": {"h": None, "s": (0, 50), "l": (60, 100)},        # 高亮度
    "dark": {"h": None, "s": (0, 100), "l": (0, 40)},          # 低亮度/暗色
    "warm": {"h": (0, 60), "s": None, "l": None},              # 暖色调(红橙黄)
    "cool": {"h": (180, 300), "s": None, "l": None},            # 冷色调(蓝绿紫)
    "high_sat": {"h": None, "s": (60, 100), "l": None},        # 高饱和
    "low_sat": {"h": None, "s": (0, 30), "l": None},           # 低饱和
}


def analyze_color_palette(image_bytes: bytes) -> Dict:
    """
    分析图片主色调
    降级方案：使用图片URL下载后分析
    需要PIL + numpy
    """
    try:
        from PIL import Image
        import numpy as np
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img = img.resize((100, 100))
        arr = np.array(img)

        # 计算平均颜色
        avg_r = arr[:, :, 0].mean()
        avg_g = arr[:, :, 1].mean()
        avg_b = arr[:, :, 2].mean()

        # RGB转HSL近似
        r, g, b = avg_r / 255, avg_g / 255, avg_b / 255
        max_c = max(r, g, b)
        min_c = min(r, g, b)
        l = (max_c + min_c) / 2

        if max_c == min_c:
            h = 0
            s = 0
        else:
            d = max_c - min_c
            s = d / (2 - max_c - min_c) if l > 0.5 else d / (max_c + min_c)
            delta = max_c - min_c
            if max_c == r:
                h = ((g - b) / delta) % 6
            elif max_c == g:
                h = (b - r) / delta + 2
            else:
                h = (r - g) / delta + 4
            h *= 60

        # 判断色调
        color_tone = "neutral"
        if l > 0.7:
            color_tone = "bright"
        elif l < 0.3:
            color_tone = "dark"
        elif s > 0.5 and (h < 60 or h > 300):
            color_tone = "warm"
        elif s > 0.5 and 180 < h < 300:
            color_tone = "cool"

        return {
            "avg_color": (round(avg_r), round(avg_g), round(avg_b)),
            "hue": round(h, 1),
            "saturation": round(s * 100, 1),
            "lightness": round(l * 100, 1),
            "color_tone": color_tone,
        }
    except Exception as e:
        logger.warning(f"颜色分析失败: {e}")
        return {"color_tone": "unknown"}


def fetch_cover_from_douyin(video_url: str) -> Optional[bytes]:
    """
    从抖音视频URL提取封面图
    通过解析分享链接获取视频信息
    """
    try:
        import requests
        headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15",
            "Referer": "https://www.douyin.com/",
        }
        resp = requests.get(
            "https://www.douyin.com/aweme/v1/web/aweme/detail/",
            params={"aweme_id": video_url.strip()},
            headers=headers,
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            video_data = data.get("aweme_detail", {}).get("video", {})
            cover_url = video_data.get("cover", {}).get("url_list", [None])[0]
            if cover_url:
                img_resp = requests.get(cover_url, headers=headers, timeout=10)
                if img_resp.status_code == 200:
                    return img_resp.content
    except Exception as e:
        logger.warning(f"抖音封面获取失败: {e}")
    return None


def extract_video_id(url: str) -> Optional[str]:
    """从抖音分享链接提取视频ID"""
    # 多种链接格式支持
    patterns = [
        r'/video/(\d+)',
        r'v.douyin\.com/(\w+)',
        r'show/(\d+)',
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None


def analyze_cover_from_url(url: str) -> Dict:
    """
    分析封面图视觉特征
    输入：图片URL或视频URL
    """
    import requests
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15",
            "Referer": "https://www.douyin.com/",
        }
        img_resp = requests.get(url, headers=headers, timeout=10)
        if img_resp.status_code == 200:
            color_info = analyze_color_palette(img_resp.content)
            composition = infer_composition_type(img_resp.content)
            return {
                "url": url,
                "color_analysis": color_info,
                "composition_type": composition,
                "status": "success",
            }
    except Exception as e:
        logger.warning(f"封面分析失败 {url}: {e}")
        return {"url": url, "status": "failed", "error": str(e)}


def full_cover_analysis(url: str) -> Dict:
    """
    对封面 URL 进行完整分析（颜色 + 构图），返回可直接入库的字段。
    供各 collector 的 save_cover 调用。
    """
    import requests
    from datetime import datetime
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15",
            "Referer": "https://www.douyin.com/",
        }
        img_resp = requests.get(url, headers=headers, timeout=15)
        if img_resp.status_code != 200:
            return None

        image_bytes = img_resp.content
        color = analyze_color_palette(image_bytes)
        composition = infer_composition_type(image_bytes)

        return {
            "url": url,
            "color_tone": color.get("color_tone", ""),
            "avg_color": str(color.get("avg_color", "")),
            "hue": color.get("hue", 0),
            "saturation": color.get("saturation", 0),
            "lightness": color.get("lightness", 0),
            "composition_type": composition,
            "text_overlay_detected": 0,
            "face_detected": 0,
            "analyzed_at": datetime.now().isoformat(),
            "status": "success",
        }
    except Exception as e:
        logger.warning(f"完整封面分析失败 {url}: {e}")
        return None


def infer_composition_type(image_bytes: bytes) -> str:
    """
    推断构图类型（降级：基于平均颜色分布）
    完整版需要更复杂的图像处理
    """
    try:
        from PIL import Image
        import numpy as np
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        w, h = img.size
        arr = np.array(img)

        # 分析四象限亮度分布
        q1 = arr[:h//2, :w//2].mean()      # 左上
        q2 = arr[:h//2, w//2:].mean()      # 右上
        q3 = arr[h//2:, :w//2].mean()       # 左下
        q4 = arr[h//2:, w//2:].mean()      # 右下

        center = arr[h//4:3*h//4, w//4:3*w//4].mean()
        overall = arr.mean()

        # 主体位置判断
        quadrants = {"left": (q1 + q3) / 2, "right": (q2 + q4) / 2,
                     "top": (q1 + q2) / 2, "bottom": (q3 + q4) / 2}
        dominant = max(quadrants, key=quadrants.get)

        # 中央是否突出
        center_dominant = center > overall * 1.15

        if center_dominant:
            return "center_composition"
        elif abs(quadrants["left"] - quadrants["right"]) > 10:
            return f"{dominant}_biased"
        else:
            return "balanced"
    except Exception as e:
        logger.warning(f"构图分析失败: {e}")
        return "unknown"


def save_cover_analysis(records: List[Dict], db_path: str = "data/tiktok_baseline.db") -> int:
    """保存封面分析结果到数据库"""
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cover_database (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT,
            video_id TEXT,
            color_tone TEXT DEFAULT '',
            avg_color TEXT DEFAULT '',
            hue REAL DEFAULT 0,
            saturation REAL DEFAULT 0,
            lightness REAL DEFAULT 0,
            composition_type TEXT DEFAULT '',
            text_overlay_detected INTEGER DEFAULT 0,
            face_detected INTEGER DEFAULT 0,
            source TEXT DEFAULT '',
            category TEXT,
            analyzed_at TEXT,
            UNIQUE(url, source)
        )
    """)
    count = 0
    for r in records:
        try:
            conn.execute("""
                INSERT OR REPLACE INTO cover_database
                (url, video_id, color_tone, avg_color, hue, saturation, lightness,
                 composition_type, text_overlay_detected, face_detected, source, category, analyzed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                r.get("url", ""), r.get("video_id", ""),
                r.get("color_tone", ""), str(r.get("avg_color", "")),
                r.get("hue", 0), r.get("saturation", 0), r.get("lightness", 0),
                r.get("composition_type", ""),
                r.get("text_overlay_detected", 0), r.get("face_detected", 0),
                r.get("source", ""), r.get("category", ""),
                r.get("analyzed_at", "")
            ))
            count += 1
        except Exception as e:
            logger.warning(f"封面分析入库失败: {e}")
    conn.commit()
    conn.close()
    return count


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    print("封面分析模块测试...")
    print("支持: URL或视频ID → 颜色分析 + 构图推断")
