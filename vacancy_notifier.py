import requests
from bs4 import BeautifulSoup
import json
import os
import schedule
import time
from datetime import datetime
import requests as req

KEYWORDS = [
    "MPSC", "SSC CGL", "SSC CHSL",
    "Income Tax", "Nagar Palika",
    "Municipal", "Aurangabad",
    "Maharashtra", "Clerk", "Tax Inspector"
]

SEEN_FILE = "seen_vacancies.json"
TELEGRAM_TOKEN = "8614189280:AAGM7a1VipS7dfTPsyM5PJzPJ3_fiR21iLw"
TELEGRAM_CHAT_ID = "1932615379"


def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return json.load(f)
    return []


def save_seen(seen_list):
    with open(SEEN_FILE, "w") as f:
        json.dump(seen_list, f)


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        req.post(url, data=data)
        print("✅ Telegram notification sent!")
    except Exception as e:
        print(f"Telegram error: {e}")


def scrape_vacancies():
    found = []
    sources = [
        {
            "name": "Sarkari Result",
            "url": "https://www.sarkariresult.com/latestjob/",
        },
        {
            "name": "MPSC",
            "url": "https://mpsc.gov.in/advertisements",
        },
    ]

    for source in sources:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(source["url"], headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            links = soup.find_all("a")

            for link in links:
                text = link.get_text(strip=True)
                href = link.get("href", source["url"])

                matched = [kw for kw in KEYWORDS if kw.lower() in text.lower()]
                if matched and "2026" in text:
                    found.append({
                        "source": source["name"],
                        "title": text[:120],
                        "link": href,
                        "keywords": matched,
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })

        except Exception as e:
            print(f"Error: {source['name']} — {e}")

    return found


def check_vacancies():
    print(f"\nChecking... {datetime.now().strftime('%H:%M:%S')}")
    seen = load_seen()
    new_vacancies = []

    results = scrape_vacancies()

    for vacancy in results:
        uid = vacancy["title"] + vacancy["source"]
        if uid not in seen:
            seen.append(uid)
            new_vacancies.append(vacancy)

    if new_vacancies:
        print(f"\n🎉 {len(new_vacancies)} NEW VACANCIES FOUND!")
        for v in new_vacancies:
            print(f"\n✅ {v['source']}")
            print(f"   {v['title']}")
            print(f"   Keywords: {', '.join(v['keywords'])}")
            print(f"   Link: {v['link']}")

            msg = (
                f"🏛 <b>NEW VACANCY ALERT!</b>\n\n"
                f"📌 {v['title']}\n\n"
                f"🔑 Keywords: {', '.join(v['keywords'])}\n"
                f"🌐 Source: {v['source']}\n"
                f"🔗 {v['link']}\n"
                f"⏰ {v['time']}"
            )
            send_telegram(msg)

        with open("vacancy_log.txt", "a") as f:
            for v in new_vacancies:
                f.write(f"\n{'='*50}\n")
                f.write(f"Time: {v['time']}\n")
                f.write(f"Source: {v['source']}\n")
                f.write(f"Title: {v['title']}\n")
                f.write(f"Link: {v['link']}\n")

        save_seen(seen)
    else:
        print("No new vacancies found.")


schedule.every().day.at("09:00").do(check_vacancies)
schedule.every().day.at("13:00").do(check_vacancies)
schedule.every().day.at("18:00").do(check_vacancies)

print("🤖 NaukriRadar Bot Started!")
print(f"Keywords: {', '.join(KEYWORDS)}")

if os.path.exists(SEEN_FILE):
    os.remove(SEEN_FILE)

check_vacancies()

while True:
    schedule.run_pending()
    time.sleep(60)