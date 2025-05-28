import os
from dotenv import load_dotenv
load_dotenv()
import requests
import time
import schedule
from datetime import datetime

# Lista URL-i do monitorowania
URLS_TO_CHECK = os.getenv("URLS_TO_CHECK", "")
URLS_TO_CHECK = [url.strip() for url in URLS_TO_CHECK.split(",") if url.strip()]

# Parametry środowiskowe
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

# Dummy HTTP server for Render (aby aplikacja działała jako Web Service)
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Monitoring bot is running")

def run_http_server():
    port = int(os.environ.get("PORT", 10000))  # Render używa zmiennej PORT
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    print(f"Running dummy server on port {port}")
    server.serve_forever()

if __name__ == "__main__":
    # Uruchom dummy serwer w tle
    threading.Thread(target=run_http_server, daemon=True).start()

    # Uruchom główną pętlę monitorującą
    main()
