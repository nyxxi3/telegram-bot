import requests
from bs4 import BeautifulSoup
import os

# Define the web scraping function
def scrape_news():
    response = requests.get("https://www.sathyabama.ac.in/")
    soup = BeautifulSoup(response.text, "html.parser")
    
    news = soup.find_all(class_="content-wrp")
    news_list = []

    for heading in news:
        title = heading.find(class_="title").getText().strip()
        date = heading.find(class_="date").getText().strip()
        link = heading.find(class_="view-more-right").find(name="a").get("href")
        full_link = "https://www.sathyabama.ac.in/" + link
        news_list.append((title, date, full_link))
    
    return news_list

# Function to send a message via Telegram
def send_telegram_message(message):
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')  # Store your token in Lambda environment variables
    chat_id = os.getenv('TELEGRAM_CHAT_ID')  # Store the chat ID in environment variables
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    payload = {'chat_id': chat_id, 'text': message}
    requests.post(url, json=payload)

# Lambda function handler
def lambda_handler(event, context):
    news_list = scrape_news()

    if news_list:
        for title, date, link in news_list:
            message = f"Title: {title}\nDate: {date}\nLink: {link}"
            send_telegram_message(message)
    else:
        send_telegram_message('No news found.')
    
    return {
        'statusCode': 200,
        'body': 'News checked and messages sent'
    }
