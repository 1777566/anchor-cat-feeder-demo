"""
角色 1（续）：数据员 —— 抓欧美用户的真实声音（YouTube 评测视频的字幕 + 评论）

为什么用 YouTube：品牌官网的评论是筛选过的（CatGenie 官网平均 4.94 星），看不到真实痛点；
YouTube 上的英文评测和评论区里，用户会说“卡粮了”“传感器误报”“App 掉线”。

运行：.venv/bin/python scripts/04_youtube.py   （需要 Clash Verge 开着，走 127.0.0.1:7897）
输出：data/youtube/<视频ID>.json，以及 data/youtube_comments.csv
"""
import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "youtube"
PROXY = "socks5h://127.0.0.1:7897"   # 本机 Clash；直连在国内访问不了 YouTube
QUERIES = [
    "self cleaning litter box review problems",
    "automatic litter box worth it",
    "PETKIT Purobot review",
    "Petlibro feeder review",
    "automatic cat feeder problems",
    "cat water fountain review",
    "smart cat litter box long term review",
    "Neakasa M1 review",
    "CATLINK litter box review",
    "smart pet camera feeder cats review",
]
PER_QUERY = 4
MAX_COMMENTS = 120


def ytdlp(*args, timeout=240):
    env = {k: v for k, v in os.environ.items() if "proxy" not in k.lower()}
    cmd = ["uvx", "--from", "yt-dlp@latest", "yt-dlp", "--no-warnings", "--proxy", PROXY, *args]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip()[-300:])
    return p.stdout


def search(q):
    raw = ytdlp(f"ytsearch{PER_QUERY}:{q}", "--flat-playlist", "--dump-json")
    return [(json.loads(l)["id"], q) for l in raw.splitlines()]


def fetch(vid):
    path = OUT / f"{vid}.json"
    if path.exists():
        return vid, "已存在"
    raw = ytdlp(f"https://www.youtube.com/watch?v={vid}", "--skip-download", "--write-comments",
                "--extractor-args", f"youtube:max_comments={MAX_COMMENTS},all,0,0;comment_sort=top",
                "--dump-json")
    info = json.loads(raw.splitlines()[-1])
    keep = {
        "id": vid, "title": info.get("title"), "channel": info.get("channel"),
        "upload_date": info.get("upload_date"), "views": info.get("view_count"),
        "url": f"https://www.youtube.com/watch?v={vid}",
        "description": (info.get("description") or "")[:1500],
        "comments": [{"text": c.get("text"), "likes": c.get("like_count"), "author": c.get("author")}
                     for c in (info.get("comments") or [])],
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    path.write_text(json.dumps(keep, ensure_ascii=False))
    return vid, f"{len(keep['comments'])} 条评论"


def _safe(vid):
    try:
        return fetch(vid)
    except Exception as e:
        return vid, f"失败：{e}"


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    found = {}
    for q in QUERIES:
        try:
            for vid, qq in search(q):
                found.setdefault(vid, qq)
        except Exception as e:
            print("搜索失败", q, e)
    print(f"共找到 {len(found)} 个不重复的视频")
    with ThreadPoolExecutor(max_workers=3) as pool:   # 低并发，礼貌抓取
        for vid, status in pool.map(lambda v: _safe(v), found):
            print(vid, status)

    rows = []
    for f in OUT.glob("*.json"):
        v = json.loads(f.read_text())
        for c in v["comments"]:
            rows.append({"video_id": v["id"], "video_title": v["title"], "channel": v["channel"],
                         "views": v["views"], "comment": c["text"], "likes": c["likes"], "url": v["url"]})
    pd.DataFrame(rows).to_csv(ROOT / "data" / "youtube_comments.csv", index=False)
    print(f"评论合计 {len(rows)} 条 → data/youtube_comments.csv")

