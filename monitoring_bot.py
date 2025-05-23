import requests
import time
from datetime import datetime

# Konfiguracja
URLS_TO_CHECK = [
    "https://dolby.okta.com/",
    "https://confluence.dolby.net/kb/",
    "https://app.smartsheet.com/",
    "https://dolby.ent.box.com/"

]
CHECK_INTERVAL_SECONDS = 300  # co 5 minut
TEAMS_WEBHOOK_URL = "https://dolby.webhook.office.com/webhookb2/da4607bf-4106-4b9d-88a1-0e8087794137@05408d25-cd0d-40c8-8962-5462de64a318/IncomingWebhook/a9bc454da51f4367bebeaaf63ecfe6c1/cc9a05af-8a0a-46a2-8400-6f60cedfeded/V2JnLzypiJ1SzShBjol9R_VfWKknkTC7bk__IA8kNL17E1"  # <- Wklej swój webhook

# Status poprzedni: True = OK, False = Błąd
status_map = {url: True for url in URLS_TO_CHECK}

def send_teams_alert(url, status, error_msg=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if status:  # przywrócono
        title = f"✅ {url} znowu działa"
        text = f"**Czas:** {timestamp}\n\nStrona działa poprawnie."
        color = "00cc66"
    else:  # awaria
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

        if not status_map[url]:  # jeśli poprzednio był błąd, a teraz OK
            send_teams_alert(url, True)
            status_map[url] = True

    except Exception as e:
        print(f"[{datetime.now()}] BŁĄD: {url} — {e}")
        if status_map[url]:  # jeśli wcześniej było OK, a teraz błąd
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
