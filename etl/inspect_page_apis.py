from __future__ import annotations

import argparse

from sources.http import fetch_html_auto


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a page and print XHR/fetch API requests.")
    parser.add_argument("url")
    parser.add_argument(
        "--fetcher",
        default="stealth",
        choices=["auto", "dynamic", "stealth", "get"],
        help="Fetch strategy. Use stealth for protected dynamic sites.",
    )
    parser.add_argument("--wait-selector", default=None)
    args = parser.parse_args()

    fr = fetch_html_auto(
        args.url,
        fetcher=args.fetcher,
        wait_selector=args.wait_selector,
        capture_api=True,
    )
    print(f"final_url={fr.final_url}")
    print(f"status_code={fr.status_code}")
    print(f"api_requests={len(fr.api_requests)}")
    for api_url in fr.api_requests:
        print(api_url)


if __name__ == "__main__":
    main()
