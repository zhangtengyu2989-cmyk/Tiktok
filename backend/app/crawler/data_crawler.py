"""
统一数据采集入口
一键从所有平台采集：BGM + 标题 + 评论 + 封面分析
"""
import logging
import sys
import os

sys.stdout.reconfigure(encoding="utf-8")

from .bgm_crawler import crawl_all as crawl_bgm, init_bgm_table
from .title_crawler import crawl_all_titles, save_titles_to_db, fetch_weibo_hot, fetch_douyin_hot_titles
from .comment_crawler import init_comment_table, seed_sample_comments, save_comments_to_db
from .xlsx_sync import get_xlsx_sync, sync_all_tables_to_xlsx

logger = logging.getLogger("tiktokrx.data_crawler")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def init_all_tables(db_path: str = "data/tiktok_baseline.db") -> None:
    """初始化所有数据表"""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    init_bgm_table(db_path)
    init_comment_table(db_path)

    import sqlite3
    conn = sqlite3.connect(db_path)
    # 标题表
    conn.execute("""
        CREATE TABLE IF NOT EXISTS title_database (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            hot_value INTEGER DEFAULT 0,
            category TEXT,
            label TEXT,
            source TEXT DEFAULT '',
            has_number INTEGER DEFAULT 0,
            has_exclaim INTEGER DEFAULT 0,
            has_emoji INTEGER DEFAULT 0,
            has_question INTEGER DEFAULT 0,
            has_suspense INTEGER DEFAULT 0,
            emotion_words INTEGER DEFAULT 0,
            title_length INTEGER DEFAULT 0,
            crawled_at TEXT,
            UNIQUE(title, source)
        )
    """)
    # 封面表
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
    conn.commit()
    conn.close()
    logger.info("所有数据表初始化完成")


def crawl_all_data(db_path: str = "data/tiktok_baseline.db") -> dict:
    """
    采集所有类型数据
    返回各类型的采集数量统计
    """
    init_all_tables(db_path)
    results = {}

    # 1. BGM数据
    logger.info("=" * 40)
    logger.info("开始采集 BGM 数据...")
    try:
        bgm_results = crawl_bgm(db_path)
        results["bgm"] = sum(bgm_results.values())
    except Exception as e:
        logger.error(f"BGM采集失败: {e}")
        results["bgm"] = 0

    # 2. 标题数据
    logger.info("=" * 40)
    logger.info("开始采集 标题 数据...")
    try:
        # 微博热搜
        weibo_titles = fetch_weibo_hot(50)
        wb_count = save_titles_to_db(weibo_titles, db_path)
        results["title_weibo"] = wb_count
        logger.info(f"微博热搜入库 {wb_count} 条")

        # 抖音热搜
        douyin_titles = fetch_douyin_hot_titles(50)
        dy_count = save_titles_to_db(douyin_titles, db_path)
        results["title_douyin"] = dy_count
        logger.info(f"抖音热搜入库 {dy_count} 条")
    except Exception as e:
        logger.error(f"标题采集失败: {e}")
        results["title_weibo"] = 0
        results["title_douyin"] = 0

    # 3. 评论数据（预置样例）
    logger.info("=" * 40)
    logger.info("开始预置 评论 样例数据...")
    try:
        seed_sample_comments(db_path)
        results["comments"] = 50  # 每个品类10条×5品类
    except Exception as e:
        logger.error(f"评论预置失败: {e}")
        results["comments"] = 0

    # 4. 最终 xlsx 同步（强制刷新所有待写入）
    logger.info("=" * 40)
    logger.info("正在同步到 xlsx...")
    try:
        db_dir = os.path.dirname(os.path.abspath(db_path))
        xlsx_dir = os.path.join(db_dir, "抖音原始数据")
        xlsx_path = sync_all_tables_to_xlsx(db_path, xlsx_dir)
        if xlsx_path:
            logger.info(f"xlsx 已更新: {xlsx_path}")
    except Exception as e:
        logger.error(f"xlsx 同步失败: {e}")

    logger.info("=" * 40)
    logger.info(f"全部采集完成！结果汇总：")
    for k, v in results.items():
        logger.info(f"  {k}: {v} 条")
    return results


def get_stats(db_path: str = "data/tiktok_baseline.db") -> dict:
    """获取各数据库的统计信息"""
    import sqlite3
    conn = sqlite3.connect(db_path)
    stats = {}
    tables = ["bgm_database", "title_database", "comment_database", "cover_database"]
    for t in tables:
        try:
            count = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            stats[t] = count
        except Exception:
            stats[t] = 0
    conn.close()
    return stats


if __name__ == "__main__":
    result = crawl_all_data()
    print("\n=== 数据库统计 ===")
    stats = get_stats()
    for k, v in stats.items():
        print(f"  {k}: {v} 条")
