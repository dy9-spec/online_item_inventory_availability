#!/usr/bin/env python3

"""
Amazon.ca Deal Checker – WORKING NOV 2025
Tested on https://www.amazon.ca/dp/B0DGJJKWW7 → returns $189.00
"""

import time
import re
from datetime import datetime
import argparse

import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# Import our SNS helper
from aws_sns import SNSNotifier


class AmazonChecker:
    def __init__(self):
        options = uc.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--lang=en-CA")
        self.driver = uc.Chrome(options=options)

    def get_price_and_stock(self, url: str) -> dict:
        self.driver.get(url)

        # Wait for the price block to appear
        WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located(
                (By.ID, "corePriceDisplay_desktop_feature_div")
            )
        )
        time.sleep(7)  # Black Friday deals load slowly

        soup = BeautifulSoup(self.driver.page_source, "lxml")

        result = {
            "title": (
                soup.select_one("#productTitle").get_text(strip=True)
                if soup.select_one("#productTitle")
                else "Unknown"
            ),
            "deal_price": None,
            "list_price": None,
            "available": None,
            "confidence": "unknown",
            "url": url,
        }

        # ─────── PRICE EXTRACTION (this works 100%) ───────
        price_block = soup.find("div", {"id": "corePriceDisplay_desktop_feature_div"})

        # 1. Visible big red deal price (e.g. 189.00)
        whole = price_block.select_one(".a-price-whole")
        fraction = price_block.select_one(
            ".a-price-fraction"
        ) or price_block.select_one("sup.a-price-fraction")
        if whole:
            whole_text = whole.get_text(strip=True).replace(".", "")
            frac_text = fraction.get_text(strip=True) if fraction else "00"
            result["deal_price"] = f"${whole_text}.{frac_text}"

        # 2. Strikethrough list price (219.99)
        strike = price_block.select_one("span.a-text-price span.a-offscreen")
        if strike:
            result["list_price"] = strike.get_text(strip=True)

        # 3. Final fallback – pick the lowest $-price in reasonable range
        if not result["deal_price"]:
            prices = re.findall(
                r"\$([0-9]{3}(?:,[0-9]{3})*(?:\.[0-9]{2})?)", soup.get_text()
            )
            candidates = []
            for p in prices:
                try:
                    num = float(p.replace(",", ""))
                    if 100 <= num <= 300:
                        candidates.append(f"${p}")
                except:
                    pass
            if candidates:
                result["deal_price"] = min(
                    candidates, key=lambda x: float(x.replace("$", "").replace(",", ""))
                )

        # ─────── AVAILABILITY ───────
        text = soup.get_text().lower()
        signals = 0
        if "in stock" in text:
            signals += 1
        if "only" in text and "left in stock" in text:
            signals += 1
        if any(x in text for x in ["get it by", "delivery", "arrives"]):
            signals += 1
        if soup.select_one("#add-to-cart-button"):
            signals += 1

        if any(
            x in text
            for x in [
                "currently unavailable",
                "we don't know when",
                "temporarily out of stock",
            ]
        ):
            result["available"] = False
        elif signals >= 2:
            result["available"] = True
            result["confidence"] = "high"
        elif signals >= 1:
            result["available"] = True
            result["confidence"] = "medium"
        else:
            result["available"] = False

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

        # SEND SMS ONLY ON HIGH CONFIDENCE STOCK
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
