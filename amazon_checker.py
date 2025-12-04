#!/usr/bin/env python3

"""
Amazon.ca Deal Checker – WORKING NOV 2025
Tested on https://www.amazon.ca/dp/B0DGJJKWW7 → returns $189.00
"""

import os
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
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-browser-side-navigation")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--remote-debugging-port=9222")
        options.add_argument("--lang=en-CA")

        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--single-process")

        # Add this line right before creating the driver
        os.environ["LANG"] = "en_CA.UTF-8"

        # Force UC to use your existing Chrome (no auto-download)
        self.driver = uc.Chrome(
            options=options,
            use_subprocess=True,  # ← crucial for launchd
            driver_executable_path=None,  # let it find Chrome itself
            browser_executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # ← explicit path
            version_main=None,  # auto-detect version
        )

    def get_price_and_stock(self, url: str) -> dict:
        self.driver.get(url)
        time.sleep(8)  # give it a moment to start loading

        soup = BeautifulSoup(self.driver.page_source, "lxml")

        result = {
            "title": "Unknown",
            "deal_price": None,
            "list_price": None,
            "available": False,
            "confidence": "unknown",
            "url": url,
        }

        # ─────── TITLE ───────
        title_el = soup.select_one("#productTitle")
        if title_el:
            result["title"] = title_el.get_text(strip=True)

        page_text = soup.get_text().lower()

        # ─────── EARLY OUT: Obvious unavailable states ───────
        unavailable_phrases = [
            "currently unavailable",
            "we don't know when or if this item will be back in stock",
            "temporarily out of stock",
            "unavailable",
            "sign up to be notified",
            "join waitlist",
        ]
        if any(phrase in page_text for phrase in unavailable_phrases):
            result["available"] = False
            result["confidence"] = "high"
            return result  # ← exit early, no need to wait for price div

        # ─────── PRICE BLOCK (only try if we think it might exist) ───────
        try:
            WebDriverWait(self.driver, 12).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "[data-asin][data-uuid]")
                )
            )
            # refresh soup after wait
            soup = BeautifulSoup(self.driver.page_source, "lxml")
            page_text = soup.get_text().lower()
        except:
            pass  # we’ll just work with whatever we have

        price_block = soup.find(
            "div", {"id": "corePriceDisplay_desktop_feature_div"}
        ) or soup.find("div", {"id": "corePrice_desktop"})

        if price_block:
            # Deal price
            whole = price_block.select_one(".a-price-whole")
            fraction = price_block.select_one(
                ".a-price-fraction"
            ) or price_block.select_one("sup.a-price-fraction")
            if whole:
                w = whole.get_text(strip=True).replace(".", "").replace(",", "")
                f = fraction.get_text(strip=True) if fraction else "00"
                result["deal_price"] = f"${w}.{f}"

            # List price (strikethrough)
            strike = price_block.select_one("span.a-text-price span.a-offscreen")
            if strike:
                result["list_price"] = strike.get_text(strip=True)

        # ─────── AVAILABILITY SIGNALS (only if we didn’t already bail) ───────
        signals = 0
        if "in stock" in page_text:
            signals += 1
        if "only " in page_text and " left in stock" in page_text:
            signals += 1
        if any(
            x in page_text for x in ["get it by", "delivery:", "arrives", "in stock on"]
        ):
            signals += 1
        if soup.select_one("#add-to-cart-button, #buybox"):
            signals += 1
        if soup.select_one('input[name="submit.add-to-cart"]'):
            signals += 1

        if signals >= 2:
            result["available"] = True
            result["confidence"] = "high"
        elif signals >= 1:
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
