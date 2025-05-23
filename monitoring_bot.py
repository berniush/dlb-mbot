import os
import requests
import time
from datetime import datetime

# Pobieranie konfiguracji ze zmiennych środowiskowych
URLS_TO_CHECK = os.getenv("URLS_TO_CHECK", "")
URLS_TO_CHECK = [url.strip() for url in URLS_TO_CHECK.split(",") if url.strip()]

CHECK_INTERVAL_SECONDS = int(os.getenv("CHECK_INTERVAL_SECONDS", "300"))
TEAMS_WEBHOOK_URL = os.getenv("TEAMS_WEBHOOK_URL")

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

def main():
    while True:
        for url in URLS_TO_CHECK:
            check_url(url)
        print("Oczekiwanie na kolejną rundę...\n")
        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
