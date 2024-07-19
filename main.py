import asyncio
import telepot
import telepot.aio
from telepot.aio.loop import MessageLoop
from pprint import pprint
from bs4 import BeautifulSoup
import requests

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

async def handle(msg):
    global chat_id
    # These are some useful variables
    content_type, chat_type, chat_id = telepot.glance(msg)
    # Log variables
    print(content_type, chat_type, chat_id)
    pprint(msg)
    username = msg['chat']['first_name']
    
    # Check that the content type is text and not the starting
    if content_type == 'text':
        if msg['text'] == '/news':
            await send_news()
        else:
            await bot.sendMessage(chat_id, 'Send /news to get the latest news.')

async def send_news():
    news_list = scrape_news()
    if news_list:
        for title, date, link in news_list:
            message = f"Title: {title}\nDate: {date}\nLink: {link}"
            await bot.sendMessage(chat_id, message)
    else:
        await bot.sendMessage(chat_id, 'No news found.')

# Program startup
TOKEN = '5914144849:AAGb6lfRC3QrDiX8255xodEY9waH4tGYKcE'
bot = telepot.aio.Bot(TOKEN)
loop = asyncio.get_event_loop()
loop.create_task(MessageLoop(bot, handle).run_forever())
print('Listening ...')

# Keep the program running
loop.run_forever()
