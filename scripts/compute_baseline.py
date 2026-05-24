"""
计算基线统计数据：从 tiktok_baseline.db 中的原始数据计算各类目的基线指标。
"""
import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "backend", "data", "tiktok_baseline.db")


def compute_baseline():
    """计算并写入 baseline_stats 表"""
    if not os.path.exists(DB_PATH):
        print(f"Database not found: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 确保 baseline_stats 表存在
    cur.execute("""
        CREATE TABLE IF NOT EXISTS baseline_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            metric_name TEXT NOT NULL,
            metric_value REAL,
            metric_json TEXT,
            UNIQUE(category, metric_name)
        )
    """)

    # 从 diagnosis_history 计算基线
    categories = ["food", "fashion", "tech", "travel", "lifestyle"]
    for cat in categories:
        cur.execute("""
            SELECT overall_score FROM diagnosis_history
            WHERE category = ?
        """, (cat,))
        rows = cur.fetchall()
        if rows:
            scores = [r[0] for r in rows if r[0] is not None]
            if scores:
                avg = sum(scores) / len(scores)
                scores_sorted = sorted(scores)
                median = scores_sorted[len(scores_sorted) // 2]
                cur.execute("""
                    INSERT OR REPLACE INTO baseline_stats (category, metric_name, metric_value)
                    VALUES (?, 'avg_score', ?)
                """, (cat, avg))
                cur.execute("""
                    INSERT OR REPLACE INTO baseline_stats (category, metric_name, metric_value)
                    VALUES (?, 'median_score', ?)
                """, (cat, median))
                print(f"  {cat}: avg={avg:.1f}, median={median:.1f}, n={len(scores)}")

    conn.commit()
    conn.close()
    print("Baseline computation complete.")


if __name__ == "__main__":
    compute_baseline()
