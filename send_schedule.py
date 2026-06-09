import datetime
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ===== 設定 =====
CALENDAR_ID   = 'ftkbb23813@gmail.com'
LINE_TOKEN    = 'uBcPae1INmcXQuluRiUkaM9BP8SFkl8q+3HpF14zDYEsARiobBDYKTV+ZVDIP30sT4q/GJ3+2MyUQUBg/wz4P0ZQaZWnjKK1mukwlMs26XgJewu5Kr6ki9H7/JJdGL94VO0wRUXBNH8oGtnL++5nDQdB04t89/1O/w1cDnyilFU='
LINE_GROUP_ID = 'Uaa69ca9ae9d9d7d221a661ab6d498496'
CREDENTIALS_FILE = 'credentials.json'
# ================

def get_tomorrow_events():
    scopes = ['https://www.googleapis.com/auth/calendar.readonly']
    creds = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE, scopes=scopes
    )
    service = build('calendar', 'v3', credentials=creds)

    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    tomorrow = now + datetime.timedelta(days=1)
    start = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
    end   = tomorrow.replace(hour=23, minute=59, second=59, microsecond=0)

    result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=start.isoformat(),
        timeMax=end.isoformat(),
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    return result.get('items', []), tomorrow

def build_message(events, tomorrow):
    date_str = tomorrow.strftime('%-m月%-d日(%a)')
    lines = [f'📅 {date_str}の予定']

    if not events:
        lines.append('予定はありません。')
    else:
        for event in events:
            start = event['start']
            if 'dateTime' in start:
                t = datetime.datetime.fromisoformat(start['dateTime'])
                time_str = t.strftime('%H:%M')
            else:
                time_str = '終日'
            lines.append(f'・{time_str}　{event["summary"]}')

    return '\n'.join(lines)

def send_line_message(text):
    url = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Authorization': f'Bearer {LINE_TOKEN}',
        'Content-Type': 'application/json'
    }
    payload = {
        'to': LINE_GROUP_ID,
        'messages': [{'type': 'text', 'text': text}]
    }
    response = requests.post(url, headers=headers, json=payload)
    print(f'LINE response: {response.status_code} {response.text}')

if __name__ == '__main__':
    events, tomorrow = get_tomorrow_events()
    message = build_message(events, tomorrow)
    print(message)
    send_line_message(message)
