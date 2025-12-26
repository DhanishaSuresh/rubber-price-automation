import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bs4 import BeautifulSoup
from datetime import date, datetime, timedelta
import re
import requests
import urllib3

from db import get_master_record, save_to_db


# ================= SSL CONFIG =================

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def safe_get(url, timeout=10):
    try:
        response = requests.get(
            url,
            timeout=timeout,
            headers=HEADERS,
            verify=False   #  SSL fix for all failing sites
        )
        response.raise_for_status()
        return response
    except Exception as e:
        print(f"Request failed for {url}: {e}")
        return None


# ================= CONSTANTS =================

MATERIALS = ["RSS4", "RSS5", "ISNR20"]

DOMESTIC_MARKETS = [
    ("col-lg-13 rb-div-style1", "loc1", "DOMESTIC", "KOTTAYAM"),
    ("col-lg-13 rb-div-style1", "loc2", "DOMESTIC", "KOCHI"),
    ("col-lg-13 rb-div-style1", "loc3", "DOMESTIC", "AGARTALA"),
]

INTERNATIONAL_MARKETS = [
    ("col-lg-18 rb-div-style1", "exloc1", "INTERNATIONAL", "BANGKOK"),
    ("col-lg-18 rb-div-style1", "exloc2", "INTERNATIONAL", "KUALALUMPUR"),
]


# ================= USD → INR =================

def get_usd_inr_rate():
    rec = get_master_record("usd-inr")
    if not rec or not rec.get("site_url"):
        print("usd-inr not configured in master")
        return None

    res = safe_get(rec["site_url"])
    if not res:
        print("USD-INR fetch failed")
        return None

    soup = BeautifulSoup(res.text, "html.parser")

    for table in soup.find_all("table"):
        header = table.find("thead")
        if not header:
            continue

        cols = [th.get_text(strip=True) for th in header.find_all("th")]
        if not any("INR for 1 USD" in c for c in cols):
            continue

        for row in table.find_all("tr"):
            tds = [td.get_text(strip=True) for td in row.find_all("td")]
            if len(tds) >= 3:
                try:
                    return float(tds[2].replace(",", ""))
                except Exception:
                    return None

    return None


# ================= RUBBER INDIA =================

def parse_rubber_table(html, div_class, city_id, market_type, market, usd_inr, rec):
    soup = BeautifulSoup(html, "html.parser")

    container = soup.find("div", class_=div_class)
    if not container:
        return []

    date_text = container.find("h4").get_text(strip=True)
    match = re.search(r'on (\d{2}-\d{2}-\d{4})', date_text)
    price_date = (
        datetime.strptime(match.group(1), "%d-%m-%Y").date()
        if match else date.today()
    )

    city_div = container.find("div", id=city_id)
    if not city_div:
        return []

    table = city_div.find("table", class_="price-table")
    if not table:
        return []

    rows = []

    def to_float(v):
        try:
            return float(v.replace(",", ""))
        except:
            return None

    for tr in table.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 3:
            continue

        material = (
            tds[0].get_text(strip=True)
            .upper()
            .replace("-", "")
            .replace(" ", "")
        )

        if material not in MATERIALS:
            continue

        inr = to_float(tds[1].get_text(strip=True))
        usd = to_float(tds[2].get_text(strip=True))

        if not inr and not usd:
            continue

        if inr:
            rows.append({
                "date": price_date,
                "material": material,
                "material_category": "NATURAL RUBBER",
                "price": inr,
                "currency": "INR",
                "market_type": market_type,
                "conversion_rate": usd_inr,
                "market": market,
                "organisation": rec["organisation"],
                "master_id": rec["id"]
            })

        if usd:
            rows.append({
                "date": price_date,
                "material": material,
                "material_category": "NATURAL RUBBER",
                "price": usd,
                "currency": "USD",
                "market_type": market_type,
                "conversion_rate": usd_inr,
                "market": market,
                "organisation": rec["organisation"],
                "master_id": rec["id"]
            })

    return rows


def scrape_rubber_india():
    rec = get_master_record("rubber-india")
    if not rec or not rec.get("site_url"):
        print("rubber-india not configured")
        return

    res = safe_get(rec["site_url"])
    if not res:
        print("Rubber India fetch failed")
        return

    html = res.text
    usd_inr = get_usd_inr_rate() or 1
    all_rows = []

    for args in DOMESTIC_MARKETS + INTERNATIONAL_MARKETS:
        rows = parse_rubber_table(html, *args, usd_inr, rec)
        all_rows.extend(rows)

    count = save_to_db(all_rows)
    print(f"rubber-india → {count} rows saved")


# ================= SGX RUBBER =================

def scrape_sgx_rubber():
    rec = get_master_record("sgx-rubber")
    if not rec or not rec.get("site_url"):
        print("sgx-rubber not configured in master")
        return

    res = safe_get(rec["site_url"])
    if not res:
        print("SGX request failed")
        return

    try:
        data = res.json()
        price = data.get("data", [{}])[0].get("preliminary-settlement-price-abs")
        price = float(price) if price else None
    except Exception:
        price = None

    if not price:
        print("sgx-rubber → no settlement price found")
        return

    usd_inr = get_usd_inr_rate()
    if not usd_inr:
        print("USD-INR rate unavailable, storing NULL")
        usd_inr = None

    rows = [{
        "date": date.today() - timedelta(days=1),
        "material": "TSR20",
        "material_category": "NATURAL RUBBER",
        "price": price,
        "currency": "USD",
        "market_type": "INTERNATIONAL",
        "conversion_rate": usd_inr,
        "market": "SINGAPORE",
        "organisation": rec["organisation"],
        "master_id": rec["id"]
    }]

    count = save_to_db(rows)
    print(f"sgx-rubber → {count} rows saved")


# ================= ENTRY =================

if __name__ == "__main__":
    site = sys.argv[1] if len(sys.argv) > 1 else None

    if site == "rubber-india":
        scrape_rubber_india()
    elif site == "sgx-rubber":
        scrape_sgx_rubber()
    else:
        scrape_rubber_india()
        scrape_sgx_rubber()
