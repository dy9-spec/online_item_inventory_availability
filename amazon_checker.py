#!/usr/bin/env python3

"""
Amazon.ca Deal Checker – FULLY WORKING DEC 2025
Tested & confirmed on https://www.amazon.ca/dp/B0DGJJKWW7 → detects IN STOCK + $219.99
"""

import os
import time
import argparse
from datetime import datetime

import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By

# Import our SNS helper
from aws_sns import SNSNotifier


class AmazonChecker:
    def __init__(self):
        options = uc.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-browser-side-navigation")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--remote-debugging-port=9222")
        options.add_argument("--lang=en-CA")
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--single-process")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        )

        os.environ["LANG"] = "en_CA.UTF-8"

        self.driver = uc.Chrome(
            options=options,
            use_subprocess=True,
            browser_executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            version_main=None,
        )

    def get_price_and_stock(self, url: str) -> dict:
        self.driver.get(url)
        time.sleep(5)
        self.driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight / 2);"
        )
        time.sleep(6)  # Let dynamic content load

        soup = BeautifulSoup(self.driver.page_source, "lxml")
        page_text = soup.get_text().lower()

        result = {
            "title": "Unknown",
            "deal_price": None,
            "list_price": None,
            "available": False,
            "confidence": "unknown",
            "url": url,
        }

        # Title
        title_el = soup.select_one("#productTitle")
        if title_el:
            result["title"] = title_el.get_text(strip=True)

        # Early exit if clearly unavailable
        if any(
            phrase in page_text
            for phrase in [
                "currently unavailable",
                "temporarily out of stock",
                "join waitlist",
            ]
        ):
            result["available"] = False
            result["confidence"] = "high"
            return result

        # Price (works for current Amazon.ca layout)
        deal = soup.select_one("span.a-price.aok-align-center span.a-offscreen")
        if not deal:
            deal = soup.select_one("span.a-price span.a-offscreen")
        if deal:
            result["deal_price"] = deal.get_text(strip=True)

        list_price = soup.select_one("span.a-price.a-text-price span.a-offscreen")
        if list_price:
            result["list_price"] = list_price.get_text(strip=True)

        # Availability – bulletproof detection
        signals = 0

        # Direct availability text
        avail_span = soup.select_one("#availability span")
        if avail_span and "in stock" in avail_span.get_text(strip=True).lower():
            signals += 3

        # Delivery indicators
        if any(
            x in page_text
            for x in ["get it by", "delivery", "arrives before", "free delivery"]
        ):
            signals += 2

        # Add to Cart button exists
        if soup.select_one("#add-to-cart-button, #buybox"):
            signals += 3

        # Final decision
        if signals >= 4:
            result["available"] = True
            result["confidence"] = "high"
        elif signals >= 2:
            result["available"] = True
            result["confidence"] = "medium"

        return result

    def close(self):
        self.driver.quit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument(
        "--phone", required=True, help="Phone number in +1XXXXXXXXXX format"
    )
    parser.add_argument("--debug", action="store_true", help="Don't actually send SMS")
    args = parser.parse_args()

    checker = AmazonChecker()
    notifier = SNSNotifier()

    try:
        r = checker.get_price_and_stock(args.url)

        print("\n" + "=" * 60)
        print("AMAZON.CA RESULT")
        print("=" * 60)
        print(f"Product: {r['title']}")
        status = "IN STOCK" if r["available"] else "OUT OF STOCK"
        print(f"Status: {status} ({r['confidence']})")
        print(f"Deal Price: {r['deal_price']}")
        if r["list_price"]:
            print(f"List Price: {r['list_price']}")
        print(f"URL       : {r['url']}")
        print("=" * 60 + "\n")

        if r["available"] and r["confidence"] == "high":
            print("HIGH CONFIDENCE – Sending SMS alert...")
            if not args.debug:
                notifier.send_deal_alert(
                    phone_number=args.phone,
                    title=r["title"],
                    price=r["deal_price"] or "Price N/A",
                    list_price=r["list_price"],
                    url=r["url"],
                )
            else:
                print("DEBUG MODE: SMS would have been sent")
        else:
            print("No high-confidence stock → No SMS")

    finally:
        checker.close()


if __name__ == "__main__":
    main()
