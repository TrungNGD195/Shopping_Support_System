import csv
import argparse


def main():
    parser = argparse.ArgumentParser(description="Build url txt from url_collection_template.csv")
    parser.add_argument("--input", default="url_collection_template.csv")
    parser.add_argument("--output", default="urls_today.txt")
    parser.add_argument("--min-priority", default="medium", choices=["low", "medium", "high"])
    args = parser.parse_args()

    priority_rank = {"low": 1, "medium": 2, "high": 3}
    min_rank = priority_rank[args.min_priority]

    urls = []
    with open(args.input, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = (row.get("product_url") or "").strip()
            status = (row.get("status") or "").strip().lower()
            priority = (row.get("priority") or "low").strip().lower()

            if not url:
                continue
            if status in {"skip", "done"}:
                continue
            if priority_rank.get(priority, 1) < min_rank:
                continue

            urls.append(url)

    with open(args.output, "w", encoding="utf-8") as f:
        for u in urls:
            f.write(u + "\n")

    print(f"Exported {len(urls)} URLs to {args.output}")


if __name__ == "__main__":
    main()
