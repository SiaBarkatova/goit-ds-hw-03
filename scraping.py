import requests
from bs4 import BeautifulSoup
import json

from bson.objectid import ObjectId

from pymongo import MongoClient
from pymongo.server_api import ServerApi


client = MongoClient(
    "mongodb+srv://goitlearn:RTwWwbuNVozx9c2b@cluster0.xrzg1kp.mongodb.net/",
    server_api=ServerApi('1')
)

db = client.book


def scrape_quotes(page: str, authors_names: list) -> dict:

    quotes_html = page.select('div.quote')

    if not quotes_html: 
        return False

    quotes = []
    authors = []

    for quote_block in quotes_html:
        author_name = quote_block.select('small.author')[0].text.strip()
        quote = {
        "tags": [tag.text.strip() for tag in quote_block.select('div.tags > a.tag')],
        "author": author_name,
        "text": quote_block.select('span.text')[0].text.strip()      
        }
        quotes.append(quote)

        if author_name not in authors_names:
            authors_names.append(author_name)
            author_url = quote_block.select('span:nth-child(2) > a')[0]["href"]    
            author = scrape_author('https://quotes.toscrape.com' + author_url)
            authors.append(author)
        
    return {
        "quotes": quotes, 
        "authors": authors
        }


def scrape_author(url: str) -> dict:
    response = requests.get(url)
    parsed_page = BeautifulSoup(response.text, 'lxml')

    author = {
        "fullname": parsed_page.select('h3.author-title')[0].text.strip(),
        "born_date": parsed_page.select('span.author-born-date')[0].text.strip(),
        "born_location": parsed_page.select('span.author-born-location')[0].text.strip(),
        "description": parsed_page.select('div.author-description')[0].text.strip()
    }
    print(f" -- Parsed author {parsed_page.select('h3.author-title')[0].text}")

    return author

def write_json(data: list, file_name: str) -> dict:
    # Open the file in write mode and use json.dump() to write the list to the file
    with open(file_name, 'w') as file:
        json.dump(data, file, indent=4)

    print(f"Data have been written to {file_name} in JSON format.")

def read_json(file_name: str) -> list:
    with open(file_name, 'r') as file:
        data = json.load(file)
    return data

def run_parsing():
    page_num = 1
    quotes = []
    authors = []
    authors_names = []
    continue_scraping = True

    while continue_scraping:
        url = f'https://quotes.toscrape.com/page/{page_num}/'
        response = requests.get(url)
        parsed_page = BeautifulSoup(response.text, 'lxml')
        
        print(f"Parsing page #{page_num}:")
        new_quotes = scrape_quotes(parsed_page, authors_names)
        if new_quotes:
            quotes += new_quotes["quotes"]
            authors += new_quotes["authors"]
            print(f"Page #{page_num} parsed successfully.")
            page_num += 1
        else:
            print(f"No more quotes. End of parsing.")
        
        continue_scraping = False

    write_json(quotes,"quotes.json")
    write_json(authors, "authors.json")

run_parsing()


quotes_read = read_json("quotes.json")
authors_read = read_json("authors.json")

#print(quotes_read)
#print(authors_read)

if isinstance(authors_read, list):
    db.authors.insert_many(authors_read)
else:
    print("No data found")

if isinstance(quotes_read, list):
    db.quotes.insert_many(quotes_read)
else:
    print("No data found")
