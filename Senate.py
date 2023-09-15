import requests
from bs4 import BeautifulSoup
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup, Tag, NavigableString
from selenium.common.exceptions import NoSuchElementException, NoSuchAttributeException, StaleElementReferenceException
import pickle
from dotenv import load_dotenv
import datetime


class transaction:
    def __init__(self, name, reportDate, transactionDate, representative, assetName, assetType, amount, transactionType,
                 Ticker, house):
        self.name = name.strip()
        self.reportDate = reportDate
        self.transactionDate = transactionDate
        self.assetName = assetName
        self.assetType = assetType
        self.transactionType = transactionType
        self.ticker = Ticker
        self.house = house

    def to_dict(self):
        return{
            'name':self.name,
            'reportDate':self.reportDate,
            'transactionDate':self.transactionDate,
            'assetName':self.assetName,
            'assetType':self.assetType,
            'ticker':self.ticker,
            'transactionType':self.transactionType,
            'house':self.house
        }

class senatePTREntry:
    def __init__(self, name, date, link: str, isPaper=False):
        self.name = name
        self.link = link
        self.date = date
        self.isPaper = isPaper
        if 'ptr' in link:
            self.isPaper = True
        self.transactions = []
        self.type = 'S'



def is_last_page(driver):
    try:
        driver.find_element(by=By.CLASS_NAME, value="next").is_enabled()
    except:
        print("is last page")


def select_next_page(driver):
    driver.find_element(by=By.CLASS_NAME, value="next").click()


def get_page_transactions(driver, url, name, date):
    transaction_list = []
    driver.get(url)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find("tbody")
    table_body = table.find_all("tr")
    for asset_transaction in table_body:
        columns = asset_transaction.find_all("td")
        transactionDate = columns[1].text
        ticker = columns[4].text
        assetName = columns[5].text
        assetType = columns[6].text
        amount = columns[8].text
        transactionType = columns[7].text
        transaction_list.append(transaction(name,
                                            date,
                                            transactionDate,
                                            None,
                                            assetName,
                                            assetType,
                                            amount,
                                            transactionType,
                                             ticker,
                                            'S'))
        print("added transactions from " + str(url))
    return transaction_list


def pull_transsaction_links(driver) -> list[senatePTREntry]:
    list_of_links = []
    table_rows = driver.find_elements(by=By.TAG_NAME, value="tr")
    driver.implicitly_wait(0.5)
    for x in table_rows:
        try:
            href = x.find_element(by=By.TAG_NAME, value="a").get_attribute("href")
            print(href)
            if "search/view/" in href:
                row_data = x.find_elements(by=By.TAG_NAME, value="td")
                isPaper = "paper" in href
                name = row_data[0].text + ' ' + row_data[1].text
                month, day, year = row_data[4].text.split('/')
                date = datetime.datetime(int(year), int(month), int(day))
                if year in ['2020', '2021', '2022', '2023']:
                    # page_url = driver.current_url
                    # page_transactions = get_page_transactions(driver,href,name,date)
                    # list_of_links.append(transaction(name,None,None,None))
                    # list_of_links.append(senatePTREntry(name, href, isPaper=False))
                    # list_of_links.append(page_transactions)
                    list_of_links.append(senatePTREntry(name, date, href, isPaper=False))

        except (NoSuchElementException, NoSuchAttributeException, StaleElementReferenceException) as e:
            print("no href")

    return list_of_links


def get_links() -> list:
    driver = webdriver.Chrome()
    driver.get('https://efdsearch.senate.gov/search/')
    driver.implicitly_wait(0.5)
    error_message_exists = True
    try:
        driver.find_element(by=By.ID, value="errorMessage")
        driver.find_element(by=By.ID, value="agree_statement").click()
    except:
        print(error_message_exists)
    driver.find_element(by=By.ID, value="reportTypeLabelPtr").click()
    driver.find_element(by=By.CLASS_NAME, value="senator_filer").click()
    driver.find_element(by=By.CLASS_NAME, value="btn-primary").click()
    full_link_list = []
    buttons = driver.find_elements(by=By.CLASS_NAME, value="a")
    max_pages = 64
    driver.implicitly_wait(0.5)
    for x in range(0, max_pages):
        list_of_data = pull_transsaction_links(driver)
        full_link_list.append(list_of_data)
        select_next_page(driver)
        time.sleep(0.5)
    return driver, full_link_list


def links_to_data(list_of_links: list[list[senatePTREntry]]) -> list[senatePTREntry]:
    for x in range(len(list_of_links)):
        for z in range(len(list_of_links[x])):
            list_of_links[x][z].scrape_data()
    pickle.dump(list_of_links, open('senate_transaction.pkl', 'wb'))
    return list_of_links

def parse_html(page_content, line_item):
    soup = BeautifulSoup(page_content, 'html.parser')
    table = soup.find("tbody")
    table_body = table.find_all("tr")
    cleaned_table_body = [x for x in table_body if type(x) == NavigableString]
    for asset_transaction in table_body:
        columns = asset_transaction.find_all("td")
        transactionDate = columns[1].text
        ticker = columns[3].text
        assetName = columns[4].text
        assetType:str = columns[5].text
        amount = columns[7].text
        transactionType = columns[6].text
        name = line_item.name
        date = line_item.date
        #transaction_type_cleaning
        transactiontype  =  "S" if "sale" in transactionType.lower()\
            else "E" if "exch" in transactionType.lower() else "P"

        if "--" not in ticker :
            line_item.transactions.append(transaction(name,
                                                        date,
                                                        transactionDate.strip(),
                                                        None,
                                                        assetName.strip(),
                                                        assetType.strip(),
                                                        amount,
                                                        transactionType.strip(),
                                                        ticker.strip(),
                                                        'S'))
            print("added transactions from " + str(line_item.link))
        else:
            print("skipped a non stock sentate transaction")
    return line_item


def parse_vision(driver, line_item):
    print("vision parsing of uploaded image " + line_item.link)
def run_senate_collection():
    driver: webdriver.Chrome()
    llist: list[list[senatePTREntry]]
    driver, llist = get_links()
    pickle.dump(llist,open('place_holder.pkl','wb'))
    for x in range(len(llist)):
        for y in range(len(llist[x])):
            line_item = llist[x][y]
            driver.get(line_item.link)
            if '/ptr/' in llist[x][y].link:
                page_content = driver.page_source
                llist[x][y] = parse_html(page_content,line_item)
            else:
                parse_vision(page_content,line_item)
    return llist