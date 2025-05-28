import os
from dotenv import load_dotenv
load_dotenv()
import requests
import time
import schedule
from datetime import datetime

URLS_TO_CHECK = os.getenv("URLS_TO_CHECK", "")
URLS_TO_CHECK = [url.strip() for url in URLS_TO_CHECK.split(",") if url.strip()]

CHECK_INTERVAL_SECONDS = int(os.getenv("CHECK_INTERVAL_SECONDS", "300"))
TEAMS_WEBHOOK_URL = os.getenv("https://dolby.webhook.office.com/webhookb2/da4607bf-4106-4b9d-88a1-0e8087794137@05408d25-cd0d-40c8-8962-5462de64a318/IncomingWebhook/f3fbd221012c4b88987a792b5bb53d52/cc9a05af-8a0a-46a2-8400-6f60cedfeded/V2Ewmi8EB0jwyrES6crn4lD417vrYZUZzHX1R9tmRenP81")

if not TEAMS_WEBHOOK_URL:
    print("Błąd: brak TEAMS_WEBHOOK_URL w zmiennych środowiskowych!")
    exit(1)

status_map = {url: True for url in URLS_TO_CHECK}

def send_teams_alert(url, status, error_msg=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if status:
        title = f"✅ {url} znowu działa"
        text = f"**Czas:** {timestamp}\n\nStrona działa poprawnie."
        color = "00cc66"
    else:
        title = f"🚨 Problem z {url}"
        text = f"**Czas:** {timestamp}\n\n**Błąd:** {error_msg}"
        color = "FF0000"

    message = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "summary": "Monitoring Alert",
        "themeColor": color,
        "title": title,
        "text": text
    }

    try:
        response = requests.post(TEAMS_WEBHOOK_URL, json=message)
        if response.status_code != 200:
            print(f"Błąd przy wysyłaniu do Teams: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Wyjątek przy wysyłaniu alertu do Teams: {e}")

def check_url(url):
    global status_map
    try:
        response = requests.get(url, timeout=10)
        if response.status_code >= 400:
            raise Exception(f"Błąd HTTP {response.status_code}")
        print(f"[{datetime.now()}] OK: {url} (status {response.status_code})")

        if not status_map[url]:
            send_teams_alert(url, True)
            status_map[url] = True

    except Exception as e:
        print(f"[{datetime.now()}] BŁĄD: {url} — {e}")
        if status_map[url]:
            send_teams_alert(url, False, str(e))
            status_map[url] = False

def send_daily_report():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text = f"**Czas:** {timestamp}\n\nDzień dobry! Oto status wszystkich stron:"
    for url in URLS_TO_CHECK:
        status = "✅ Działa" if status_map[url] else "❌ Niedostępna"
        text += f"\n- {url} — {status}"

    message = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "summary": "Daily Report",
        "themeColor": "0076D7",
        "title": "🕘 Raport dzienny",
        "text": text
    }

    try:
        response = requests.post(TEAMS_WEBHOOK_URL, json=message)
        if response.status_code != 200:
            print(f"Błąd przy wysyłaniu raportu do Teams: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Wyjątek przy wysyłaniu raportu do Teams: {e}")

def main():
    # Harmonogram raportów
    schedule.every().day.at("09:00").do(send_daily_report)
    schedule.every().day.at("16:00").do(send_daily_report)

    while True:
        for url in URLS_TO_CHECK:
            check_url(url)

        # Sprawdzanie zaplanowanych zadań
        schedule.run_pending()

        print("Oczekiwanie na kolejną rundę...\n")
        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
