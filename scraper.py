import asyncio
import subprocess
import time
import os
import sys
import json
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from datetime import datetime

# -------------------------------
# Configuration
# -------------------------------
APP_ID = 553850
DEPOTS = [553851, 553853, 553854]
MANIFEST_FILE = "manifests.json"
EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
DEBUG_PORT = 9222
STEAMDB_HOME = "https://steamdb.info/"

# -------------------------------
# Load existing manifests
# -------------------------------
if os.path.exists(MANIFEST_FILE):
    with open(MANIFEST_FILE, "r") as f:
        manifests = json.load(f)
else:
    manifests = {}

# -------------------------------
# Merge manifests to carry forward missing depots
# -------------------------------
def merge_manifests(manifests):
    sorted_dates = sorted(manifests.keys(), key=lambda x: datetime.strptime(x, "%Y-%m-%d"))
    last_known = {}
    for date in sorted_dates:
        entry = manifests[date]
        for depot in DEPOTS:
            if str(depot) not in entry and str(depot) in last_known:
                entry[str(depot)] = last_known[str(depot)]
        for depot in DEPOTS:
            if str(depot) in entry:
                last_known[str(depot)] = entry[str(depot)]
    return manifests

# -------------------------------
# Normalize SteamDB date string
# -------------------------------
def normalize_date(date_str):
    try:
        dt = datetime.strptime(date_str.replace("–", "-").strip(), "%d %B %Y - %H:%M:%S UTC")
        return dt.strftime("%Y-%m-%d")
    except Exception:
        try:
            dt = datetime.strptime(date_str.strip(), "%d %B %Y")
            return dt.strftime("%Y-%m-%d")
        except Exception:
            print(f"Warning: Could not parse date '{date_str}', leaving as-is")
            return date_str

# -------------------------------
# Launch Edge for manual login
# -------------------------------
def launch_edge_for_login():
    subprocess.run(["taskkill", "/IM", "msedge.exe", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    edge_process = subprocess.Popen([
        EDGE_PATH,
        f"--remote-debugging-port={DEBUG_PORT}",
        "--remote-debugging-address=127.0.0.1",
        "--no-first-run",
        "--no-default-browser-check",
        STEAMDB_HOME
    ])
    print(f"Edge launched at {STEAMDB_HOME}.")
    time.sleep(2)
    return edge_process

# -------------------------------
# Scrape depot manifests page
# -------------------------------
async def scrape_depot_manifests(page, depot_id):
    url = f"https://steamdb.info/depot/{depot_id}/manifests/"
    await page.goto(url)
    try:
        await page.wait_for_selector("table.table tbody tr", timeout=60000)
    except:
        print(f"Table not found for depot {depot_id}. Make sure the page loaded correctly.")
    return await page.content()

# -------------------------------
# Parse HTML table into manifest dict
# -------------------------------
def parse_table(html, depot_id):
    soup = BeautifulSoup(html, "html.parser")
    table = None
    for t in soup.find_all("table", class_="table"):
        headers = [th.text.strip().lower() for th in t.find_all("th")]
        if "seen date" in headers and "manifestid" in headers:
            table = t
            break
    if not table or not table.tbody:
        print(f"No correct table found for depot {depot_id}")
        return {}

    depot_data = {}
    for row in table.tbody.find_all("tr"):
        cols = row.find_all("td")
        if len(cols) < 3:
            continue
        raw_date = cols[0].text.strip()
        date_str = normalize_date(raw_date)
        manifest_id = cols[2].text.strip()
        depot_data[date_str] = manifest_id
    return depot_data

# -------------------------------
# Scrape patch titles
# -------------------------------
async def scrape_patch_titles(page):
    url = f"https://steamdb.info/app/{APP_ID}/patchnotes/"
    await page.goto(url)
    try:
        await page.wait_for_selector("#js-builds tr", timeout=60000)
    except:
        print("Patch notes table not found. Make sure the page loaded correctly.")
        return {}

    html = await page.content()
    soup = BeautifulSoup(html, "html.parser")
    patch_table = soup.find("tbody", id="js-builds")
    if not patch_table:
        print("No correct patch notes table found.")
        return {}

    patch_titles = {}
    for row in patch_table.find_all("tr"):
        cols = row.find_all("td")
        if len(cols) < 4:
            continue
        raw_date = cols[0].get_text(strip=True)
        title = cols[3].get_text(strip=True)
        if raw_date and title:
            date_str = normalize_date(raw_date)
            patch_titles[date_str] = title
    return patch_titles

# -------------------------------
# Main scraper routine
# -------------------------------
async def main():

    edge_process = launch_edge_for_login()

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{DEBUG_PORT}")
        context = browser.contexts[0]
        page = await context.new_page()

        for depot in DEPOTS:
            print(f"Scraping depot {depot}...")
            html = await scrape_depot_manifests(page, depot)
            depot_data = parse_table(html, depot)
            for date, manifest in depot_data.items():
                if date not in manifests:
                    manifests[date] = {}
                manifests[date][str(depot)] = manifest

        print("Scraping patch titles...")
        patch_titles = await scrape_patch_titles(page)
        for date, title in patch_titles.items():
            if date not in manifests:
                manifests[date] = {}
            manifests[date]["patch_title"] = title

        await browser.close()

        try:
            edge_process.terminate()
            edge_process.wait(timeout=5)
        except Exception:
            pass

        subprocess.run(["taskkill", "/IM", "msedge.exe", "/F"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    manifests.update(merge_manifests(manifests))

    with open(MANIFEST_FILE, "w") as f:
        json.dump(manifests, f, indent=4)

    print(f"\nUpdated {MANIFEST_FILE} with {len(manifests)} dates.\n")

# -------------------------------
# Entry point for standalone use
# -------------------------------
if __name__ == "__main__":
    asyncio.run(main())
