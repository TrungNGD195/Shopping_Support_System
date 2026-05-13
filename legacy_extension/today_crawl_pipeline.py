"""
Pipeline crawl trong ngay cho Shopping Support System.

Muc tieu:
- Giam nguy co bi block khi crawl nhieu URL.
- Tu dong crawl Tiki (rui ro thap).
- Chia session thu cong cho Shopee/Lazada (rui ro cao hon).
- Gop JSON -> 1 CSV utf-8-sig, loc comment rong/icon-only ngay luc xuat.

Cach dung nhanh:
1) Tao file urls.txt (moi dong 1 URL)
2) python today_crawl_pipeline.py plan --url-file urls.txt
3) python today_crawl_pipeline.py run-tiki --url-file urls.txt --output data/raw_data.csv
4) Sau khi crawl Shopee/Lazada bang extension, tai JSON vao 1 thu muc,
   roi chay: python today_crawl_pipeline.py merge-json --json-dir "C:/Users/<you>/Downloads" --output data/raw_data.csv
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import random
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from crawlers.tiki_crawler import TikiCrawler


VI_TEXT_RE = re.compile(r"[0-9A-Za-zA-Za-z\u00C0-\u1EF9]")


@dataclass
class UrlItem:
    url: str
    platform: str


def detect_platform(url: str) -> str:
    u = url.lower()
    if "tiki.vn" in u:
        return "tiki"
    if "shopee.vn" in u:
        return "shopee"
    if "lazada.vn" in u:
        return "lazada"
    return "unknown"


def load_urls(url_file: str) -> List[UrlItem]:
    rows: List[UrlItem] = []
    with open(url_file, "r", encoding="utf-8") as f:
        for line in f:
            url = line.strip()
            if not url or url.startswith("#"):
                continue
            rows.append(UrlItem(url=url, platform=detect_platform(url)))
    return rows


def is_meaningful_comment(text: str) -> bool:
    if text is None:
        return False
    s = str(text).strip()
    if not s:
        return False

    # Loai bo ky tu xuong dong / khoang trang de test icon-only.
    compact = re.sub(r"\s+", "", s)
    if not compact:
        return False

    # Neu khong co chu/so tieng Viet -> xem nhu icon-only.
    return bool(VI_TEXT_RE.search(compact))


def normalize_row(
    platform: str,
    product_id: str,
    review_id: str,
    rating: Optional[int],
    comment: str,
    username: str,
    date_value: str,
    source_url: str,
) -> Optional[Dict[str, str]]:
    # Lọc comment trống/icon, nhưng giữ lại toàn bộ (không lọc) nếu là sản phẩm sách
    if not is_meaningful_comment(comment):

        return None

    return {
        "platform": platform,
        "product_id": str(product_id or ""),
        "review_id": str(review_id or ""),
        "rating": "" if rating is None else str(rating),
        "comment": str(comment).strip().replace("\r", " ").replace("\n", " "),
        "username": str(username or "").strip(),
        "date": str(date_value or "").strip(),
        "source_url": str(source_url or "").strip(),
        "collected_at": datetime.now().isoformat(timespec="seconds"),
    }


def write_csv(rows: List[Dict[str, str]], output_file: str) -> None:
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "platform",
        "product_id",
        "review_id",
        "rating",
        "comment",
        "username",
        "date",
        "source_url",
        "collected_at",
    ]
    with open(output_file, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def dedupe_rows(rows: Iterable[Dict[str, str]]) -> List[Dict[str, str]]:
    seen = set()
    out = []
    for r in rows:
        key = (
            r.get("platform", ""),
            r.get("product_id", ""),
            r.get("review_id", ""),
            r.get("comment", ""),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def split_sessions(urls: List[str], per_session: int) -> List[List[str]]:
    return [urls[i : i + per_session] for i in range(0, len(urls), per_session)]


def cmd_plan(args: argparse.Namespace) -> None:
    items = load_urls(args.url_file)
    tiki = [x.url for x in items if x.platform == "tiki"]
    shopee = [x.url for x in items if x.platform == "shopee"]
    lazada = [x.url for x in items if x.platform == "lazada"]
    unknown = [x.url for x in items if x.platform == "unknown"]

    shopee_sessions = split_sessions(shopee, args.shopee_per_session)
    lazada_sessions = split_sessions(lazada, args.lazada_per_session)

    plan = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "total_urls": len(items),
        "counts": {
            "tiki": len(tiki),
            "shopee": len(shopee),
            "lazada": len(lazada),
            "unknown": len(unknown),
        },
        "sessions": {
            "shopee": shopee_sessions,
            "lazada": lazada_sessions,
        },
        "notes": [
            "Tiki: co the chay tu dong ca lo trong ngay.",
            "Shopee/Lazada: nen chay theo session, nghi 10-20 phut giua cac session.",
            "Neu bi unusual traffic: dung ngay, doi IP/mang, tiep tuc sau 20-30 phut.",
        ],
    }

    Path(args.plan_out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.plan_out, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)

    print("=== CRAWL PLAN TODAY ===")
    print(f"Tong URL: {len(items)}")
    print(f"Tiki: {len(tiki)} | Shopee: {len(shopee)} | Lazada: {len(lazada)} | Unknown: {len(unknown)}")
    print(f"Shopee sessions: {len(shopee_sessions)} (moi session toi da {args.shopee_per_session} URL)")
    print(f"Lazada sessions: {len(lazada_sessions)} (moi session toi da {args.lazada_per_session} URL)")
    print(f"Da luu plan: {args.plan_out}")



def cmd_run_tiki(args: argparse.Namespace) -> None:
    items = load_urls(args.url_file)
    tiki_urls = [x.url for x in items if x.platform == "tiki"]
    if not tiki_urls:
        print("Khong co URL Tiki trong file.")
        return

    crawler = TikiCrawler()
    rows: List[Dict[str, str]] = []

    for idx, url in enumerate(tiki_urls, start=1):
        print(f"\n[Tiki {idx}/{len(tiki_urls)}] {url}")
        try:
            result = crawler.crawl_all_reviews(url, max_reviews=args.max_reviews_per_product)
            if "error" in result:
                print(f"  -> Loi: {result['error']}")
                continue

            product_id = result.get("product_id")
            source_url = result.get("url", url)
            for rv in result.get("reviews", []):
                row = normalize_row(
                    platform="tiki",
                    product_id=str(product_id or ""),
                    review_id=str(rv.get("review_id") or ""),
                    rating=rv.get("rating_star"),
                    comment=rv.get("comment", ""),
                    username=rv.get("author_username", ""),
                    date_value=rv.get("date") or "",
                    source_url=source_url,
                )
                if row:
                    rows.append(row)

            # Delay ngau nhien de giong traffic nguoi dung
            wait_s = random.uniform(args.min_delay, args.max_delay)
            print(f"  -> Sleep {wait_s:.1f}s")
            time.sleep(wait_s)
        except Exception as ex:
            print(f"  -> Loi bat ngo: {ex}")

    rows = dedupe_rows(rows)
    write_csv(rows, args.output)
    print(f"\nDone. Da xuat {len(rows)} dong vao: {args.output}")



def parse_extension_json_file(path: str) -> Tuple[List[Dict[str, str]], int]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    rows: List[Dict[str, str]] = []
    skipped = 0

    platform = str(data.get("platform") or "").strip().lower()
    source_url = str(data.get("url") or "")

    # Lazada extension format
    if platform == "lazada" or "itemId" in data:
        product_id = str(data.get("itemId") or data.get("item_id") or "")
        for rv in data.get("reviews", []):
            row = normalize_row(
                platform="lazada",
                product_id=product_id,
                review_id=str(rv.get("id") or rv.get("reviewRateId") or ""),
                rating=rv.get("rating"),
                comment=rv.get("content", ""),
                username=rv.get("buyerName", ""),
                date_value=rv.get("reviewTime", ""),
                source_url=source_url,
            )
            if row:
                rows.append(row)
            else:
                skipped += 1
        return rows, skipped

    # Shopee extension format
    if "shopid" in data and "itemid" in data:
        product_id = f"{data.get('shopid')}_{data.get('itemid')}"
        for rv in data.get("reviews", []):
            row = normalize_row(
                platform="shopee",
                product_id=product_id,
                review_id=str(rv.get("cmtid") or rv.get("orderid") or ""),
                rating=rv.get("rating_star"),
                comment=rv.get("comment", ""),
                username=rv.get("author_username", ""),
                date_value=rv.get("date") or "",
                source_url=source_url,
            )
            if row:
                rows.append(row)
            else:
                skipped += 1
        return rows, skipped

    # Tiki json format tu crawler
    if (data.get("platform") == "tiki") and ("reviews" in data):
        product_id = str(data.get("product_id") or "")
        source_url = str(data.get("url") or "")
        for rv in data.get("reviews", []):
            row = normalize_row(
                platform="tiki",
                product_id=product_id,
                review_id=str(rv.get("review_id") or rv.get("id") or ""),
                rating=rv.get("rating_star") or rv.get("rating"),
                comment=rv.get("comment", "") or rv.get("content", ""),
                username=rv.get("author_username", "") or rv.get("buyerName", ""),
                date_value=rv.get("date") or rv.get("reviewTime") or "",
                source_url=source_url,
            )
            if row:
                rows.append(row)
            else:
                skipped += 1
        return rows, skipped

    return [], 0



def cmd_merge_json(args: argparse.Namespace) -> None:
    pattern = os.path.join(args.json_dir, "*.json")
    files = glob.glob(pattern)
    if not files:
        print(f"Khong tim thay json nao trong: {args.json_dir}")
        return

    all_rows: List[Dict[str, str]] = []
    total_skipped = 0

    for fp in files:
        try:
            rows, skipped = parse_extension_json_file(fp)
            total_skipped += skipped
            if rows:
                all_rows.extend(rows)
                print(f"[OK] {Path(fp).name}: +{len(rows)} rows")
        except Exception as ex:
            print(f"[SKIP] {Path(fp).name}: {ex}")

    all_rows = dedupe_rows(all_rows)
    write_csv(all_rows, args.output)

    print("\n=== MERGE SUMMARY ===")
    print(f"Files scanned: {len(files)}")
    print(f"Rows exported: {len(all_rows)}")
    print(f"Rows filtered (rong/icon-only): {total_skipped}")
    print(f"CSV output: {args.output}")



def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Pipeline crawl toi uu trong ngay")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_plan = sub.add_parser("plan", help="Lap ke hoach chay trong ngay")
    p_plan.add_argument("--url-file", required=True, help="File txt chua URL")
    p_plan.add_argument("--shopee-per-session", type=int, default=8)
    p_plan.add_argument("--lazada-per-session", type=int, default=4)
    p_plan.add_argument("--plan-out", default="data/crawl_plan_today.json")
    p_plan.set_defaults(func=cmd_plan)

    p_tiki = sub.add_parser("run-tiki", help="Tu dong crawl URL Tiki")
    p_tiki.add_argument("--url-file", required=True, help="File txt chua URL")
    p_tiki.add_argument("--output", default="data/raw_data_tiki.csv")
    p_tiki.add_argument("--max-reviews-per-product", type=int, default=3000)
    p_tiki.add_argument("--min-delay", type=float, default=1.5)
    p_tiki.add_argument("--max-delay", type=float, default=3.5)
    p_tiki.set_defaults(func=cmd_run_tiki)

    p_merge = sub.add_parser("merge-json", help="Gop JSON da crawl thanh 1 CSV")
    p_merge.add_argument("--json-dir", required=True, help="Thu muc chua file JSON")
    p_merge.add_argument("--output", default="data/raw_data.csv")
    p_merge.set_defaults(func=cmd_merge_json)

    return p



def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
