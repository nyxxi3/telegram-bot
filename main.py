import requests
from bs4 import BeautifulSoup
import os
import boto3
import json
import time

s3 = boto3.client('s3')
BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

def lambda_handler(event, context):
    check_for_new_news()
    while True:
        try:
            process_telegram_updates()
            time.sleep(10)
        except Exception as e:
            print(f"Error in lambda_handler: {e}")
            time.sleep(60)

def process_telegram_updates():
    url = f'https://api.telegram.org/bot{TOKEN}/getUpdates'
    response = requests.get(url)
    updates = response.json().get('result', [])
    
    for update in updates:
        chat_id = update['message']['chat']['id']
        text = update['message'].get('text', '').lower()

        if text == '/start':
            send_telegram_message(chat_id, "Welcome! You've been registered. Use /news to get the latest news.")
            save_chat_id(chat_id)
        elif text == '/news':
            send_news(chat_id)
        else:
            send_telegram_message(chat_id, "Please use /news to get the latest news.")

        requests.get(f'{url}?offset={update["update_id"] + 1}')

def send_news(chat_id):
    try:
        response = s3.get_object(Bucket=BUCKET_NAME, Key='news.json')
        news = json.loads(response['Body'].read().decode('utf-8'))
        if news:
            message = "Current News:\n\n"
            for title, date, link in news:
                message += f"Title: {title}\nDate: {date}\nLink: {link}\n\n"
            send_telegram_message(chat_id, message)
        else:
            send_telegram_message(chat_id, "No news available at the moment.")
    except s3.exceptions.NoSuchKey:
        send_telegram_message(chat_id, "No news available at the moment.")
    except json.JSONDecodeError:
        send_telegram_message(chat_id, "Error retrieving news. Please try again later.")

def check_for_new_news():
    current_news = scrape_news()
    previous_news = get_previous_news()
    if current_news != previous_news:
        s3.put_object(Bucket=BUCKET_NAME, Key='news.json', Body=json.dumps(current_news).encode('utf-8'))
        notify_users_of_new_news(current_news)

def notify_users_of_new_news(news):
    chat_ids = get_chat_ids()
    if not chat_ids:
        return
    message = "New News:\n\n"
    for title, date, link in news:
        message += f"Title: {title}\nDate: {date}\nLink: {link}\n\n"
    
    for chat_id in chat_ids:
        send_telegram_message(chat_id, message)


def send_telegram_message(chat_id, message):
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    payload = {'chat_id': chat_id, 'text': message}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error sending message to {chat_id}: {e}")

def save_chat_id(chat_id):
    chat_ids = get_chat_ids()
    if chat_id not in chat_ids:
        chat_ids.append(chat_id)
        s3.put_object(Bucket=BUCKET_NAME, Key='chat_ids.json', Body=json.dumps(chat_ids).encode('utf-8'))

def get_chat_ids():
    try:
        response = s3.get_object(Bucket=BUCKET_NAME, Key='chat_ids.json')
        return json.loads(response['Body'].read().decode('utf-8'))
    except s3.exceptions.NoSuchKey:
        return []
    except json.JSONDecodeError:
        return []

def scrape_news():
    response = requests.get("https://www.sathyabama.ac.in/")
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    news = soup.find_all(class_="content-wrp")
    current_news = []
    for heading in news:
        title = heading.find(class_="title").getText().strip()
        date = heading.find(class_="date").getText().strip()
        link = heading.find(class_="view-more-right").find(name="a").get("href")
        full_link = "https://www.sathyabama.ac.in/" + link
        current_news.append((title, date, full_link))
    return current_news

def get_previous_news():
    try:
        response = s3.get_object(Bucket=BUCKET_NAME, Key='news.json')
        return json.loads(response['Body'].read().decode('utf-8'))
    except s3.exceptions.NoSuchKey:
        return []
    except json.JSONDecodeError:
        return []
