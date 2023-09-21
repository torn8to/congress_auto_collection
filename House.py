import datetime
import os
import pickle
import sys
import tempfile
import zipfile
from Senate import transaction
import pandas as pd
import requests
import io
from pathlib import Path
import aspose.words as aw
from bs4 import BeautifulSoup
import pikepdf
from pdf2image import convert_from_path
from pdf2image.exceptions import (PDFSyntaxError, PDFPageCountError,PDFInfoNotInstalledError)
from pytesseract import pytesseract
from img2table.document import Image
from img2table.ocr import EasyOCR
import numpy as np
import cv2 as cv
import os
from dotenv import load_dotenv
import yfinance as yf
from loguru import logger
import multiprocessing


load_dotenv()
tesseract = EasyOCR(lang=['en'])
unran_documents = []
log_file_path = './log/log'
class housePTRentry:
    def __init__(self, name, link, representative, isPaper=False):
        self.name = name
        self.link = link
        self.representative = representative
        self.isPaper = isPaper
        self.transactions = []
        self.type = 'H'

    def setPaper(self,paper = True):
        self.isPaper=paper

def grab_document(year:int or str,DocID:str,tmp: tempfile.TemporaryDirectory):
     base_string = "https://disclosures-clerk.house.gov/public_disc/ptr-pdfs"
     full_string = base_string + "/" + str(year) + "/" + str(DocID) + ".pdf"
     r = requests.get(full_string)
     filename = Path(tmp.name + str(year) + str(DocID) + '.pdf')
     print(filename)
     with open(filename,'wb') as file:
         file.write(r.content)
     return filename, full_string


def get_type(line_item:str):
    open_bracket = line_item.index(r'[') + 1
    close_bracket = line_item.index(r']')
    category = line_item[open_bracket:close_bracket]
    print(category)
    return category

def get_name(ticker:str):
    try:
        data = yf.Ticker(ticker)
        return data.info['longName']
    except:
        return None


def get_ticker(self, line_item):
    open_bracket = line_item.index(r'(') + 1
    close_bracket = line_item.index(r')')
    category = line_item[open_bracket:close_bracket]
    return category


def get_amount(line_item):
    first_money = line_item.split(" ")
    val = None
    amount = None
    x:str
    for x in first_money:
        if '$' in x:
            try:
                index = x.index('$')
                next:str = x[index+1]
                if next.isnumeric():
                    val = x
                    break
            except Exception:
                pass
    amount_type = {
            "$1,001": "$1,001-$15,000",
            "$15,000": "$1,001-$15,000",
            "$15,001": "$15,001-$50,000",
            "$50,001": "$50,001-$100,000",
            "$100,001": "$100,001-$250,000",
            "$250,001": "$250,001-$500,000",
            "$500,001": "$500,001-$1,000,000"
        }
    amount = amount_type.get(val,"$0-$1,000")
    print(amount)
    return amount


def get_account_type(line_item):
     account_type = line_item[4:6]
     if account_type == 'JT' or account_type == 'SP':
        return account_type
     return ''


def get_transaction_type(line_item):
        res = []
        for x in line_item.split(" "):
            if len(x) == 1:
                res.append(x)
        transaction_type = 'P'
        for x in res:
            if x.lower().find("s") > -1:
                transaction_type = "S"
                break
            elif x.lower().find("e") > -1:
                transaction_type = "S"
                break
        for x in line_item.split(" "):
            if len(x) == 2:
                res.append(x)
        for x in res:
            if x.lower().find("PS") > -1:
                transaction_type = "S"
        return transaction_type


def get_transaction_and_report_date(line_item:str):
    desired_character = "/"
    limit_on_search = 4
    list_of_indexes = []
    transactionDate:str or datetime.datetime or datetime.date = None
    reportDate:str or datetime.datetime or datetime.date = None
    '''
    print(list_of_indexes)
    print(line_item)
    for x in range(len(line_item)):
        if len(list_of_indexes) == limit_on_search:
            break
        try:
            index = line_item.index(desired_character)
            back_slash = r'\\'
            line_item.replace('/', back_slash)
            list_of_indexes.append(index)
        except:
            break
    print(list_of_indexes)
    if len(list_of_indexes) == 4:
        if list_of_indexes[0]+3 == list_of_indexes[1]:
            transactionDate = line_item[list_of_indexes[0]-3:list_of_indexes[0]+5]
        if list_of_indexes[2]+3 == list_of_indexes[3]:
            reportDate = line_item[list_of_indexes[0]-3:list_of_indexes[0]+5]
    '''
    first_occurence = line_item.index("/")
    last_occurence = line_item.rindex("/")
    transactionDate = line_item[first_occurence-2:first_occurence+8]
    reportDate = line_item[last_occurence-5:last_occurence+5]
    return transactionDate, reportDate

def get_transaction_date(line_item):
    return get_transaction_and_report_date(line_item)[0]

def get_report_date(line_item):
    return get_transaction_and_report_date(line_item)[1]

def get_ticker_inline(line_item):
    open = line_item.index("(")
    close = line_item.index(")")
    return line_item[open+1:close]
def parse_stock_default(house_entry:housePTRentry ,line_item):
    ticker = get_ticker_inline(line_item)
    print(ticker)
    return transaction(house_entry.name,
                       get_report_date(line_item),
                       get_transaction_date(line_item),
                       house_entry.representative,
                       get_name(ticker),
                       get_type(line_item),
                       get_amount(line_item),
                       get_transaction_type(line_item),
                       ticker,
                       "H")


def parse_other(line_item):
    pass



def invalid(kwargs):
    pass


def determine_document_type(file_location):
    soup = BeautifulSoup(open(file_location,encoding="utf-8"),'html.parser')
    body = soup.find("body")
    title = None
    try:
        p_list = body.find("table")
        title = True
    except:
        print("Mail in document")
    if title != None:
        return 'ClASSIC_PTR'
    else:
        return 'MAIL_IN_PTR'


def parse_html(file_location:str, pdf_location:str,house_entry):
    logger.info("started to parse html for house entry:"+house_entry.link)
    data_text ="font-size:"
    doc_type = determine_document_type(file_location)
    switcher ={
             'ClASSIC_PTR': parse_classic,
             "MAIL_IN_PTR": parse_mail_in,
            }
    func = switcher.get(doc_type)
    return func(file_location, pdf_location, house_entry)


def parse_classic(file_location:str, pdf_location:str,house_entry:housePTRentry = housePTRentry("name","link","representative",isPaper=False)):
    transaction_list = []
    try:
        soup = BeautifulSoup(open(file_location,encoding='UTF-8'), 'html.parser')
    except:
        unran_documents.append(house_entry)
        return None
    tables = soup.find('tbody')
    table_rows = soup.find_all('tr')
    buffer = table_rows
    for x in table_rows:
        if ":" in x.getText():
            table_rows.remove(x)
        l = []
        for x in buffer:
            l.append(x.text)
        result = []
        [result.append(x) for x in l if "D:" not in x]
        result.pop(0)

    try:
        for x in result:
            if '[ST]' in x:
                transaction_list.append(parse_stock_default(house_entry,line_item=x))
    except:
        house_entry.setPaper()
        unran_documents.append(house_entry)
        return None
    house_entry.transactions = transaction_list
    return house_entry


def parse_mail_in(file_location, pdf_location,house_entry:housePTRentry):
    #pdf_images = convert_from_path(pdf_location, dpi=400)
    unran_documents.append(house_entry.link)



def spread_sheet_prep():
    pass



def parse_spread_sheet(images,):
    """
    CONVERT TABLES to data frames
    :param images: iamges of the pdf forms
    """
    for x in images:
        x.convert('RGB')
        cv_image = cv.cvtColor(np.array(x))
        t = tempfile.NamedTemporaryFile()
        cv.imwrite(t)
        doc = Image(t)
        extracted_tables = doc.extract_tables(ocr=tesseract,
                                              implicit_rows=False,
                                              borderless_tables=False,
                                              min_confidence=50)
        print(extracted_tables)

def parse_string(line_item: str):
    type = get_type(line_item)
    switcher = {
        'ST': parse_stock_default,
    }
    func = switcher.get(type, lambda: invalid)
    return func(line_item)


def get_mail_in_spreadsheet(self, Images):
    list_of_transactions = []
    for x in Images:
        pass


def get_ticker_by_search(company_name):
    yfinance = "https://query2.finance.yahoo.com/v1/finance/search"
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
    params = {"q": company_name, "quotes_count": 1, "country": "United States"}
    res = requests.get(url=yfinance, params=params, headers={'User-Agent': user_agent})
    data = res.json()
    company_code = data['quotes'][0]['symbol']


def bulkHouseCollection():
    logger.add(sys.stderr,format="<red>[{level}]</red> Message: <green>{message}</green> @ time:{time}", colorize=True, enqueue=False)
    ptr_temp_directory = tempfile.TemporaryDirectory()
    data:pd.DataFrame = pd.DataFrame()
    transaction_data = []
    with tempfile.TemporaryDirectory() as temp:
        avaliable_years = ['2020', '2021', '2022', '2023']
        for year in avaliable_years:
            req = requests.get('https://disclosures-clerk.house.gov/public_disc/financial-pdfs/' + year + 'FD.ZIP')
            if req.ok:
                zip = zipfile.ZipFile(io.BytesIO(req.content))
                zip.extractall(temp)
        print(os.listdir(temp))
        # asd = requests.get('https://disclosures-clerk.house.gov/public_disc/financial-pdfs/2022FD.ZIP', stream=True)
        frames = []
        for year in avaliable_years:
            frames.append(pd.read_csv(temp + '/' + year + 'FD.txt', sep="\t", header=0))
        data = pd.concat(frames)
        document_type_filtering = data[data['FilingType'] == 'P']
    logger.success("bulk_data_gathered")
    pickle.dump(document_type_filtering,open('old_trades.pkl', 'wb'))

    for x in range(document_type_filtering.shape[0]):
        doc_id = document_type_filtering.iloc[x]['DocID']
        year = document_type_filtering.iloc[x]['Year']
        first_name = document_type_filtering.iloc[x]['First'] + ' '
        last_name = document_type_filtering.iloc[x]['Last']
        name = first_name + last_name
        filename, url = grab_document(year, doc_id, ptr_temp_directory)
        house = housePTRentry(name, link=url, representative=False)
        doc = aw.Document(filename.__str__())
        doc.save('./dump_directory/file' + str(x) + '.html')
        transaction_data.append(parse_html('./dump_directory/file' + str(x) + '.html', filename.__str__(), house))
    link_list = []
    transaction_list = []
    not_parseable =[]
    for x in transaction_data:
        if type(x) == housePTRentry:
            if x.isPaper==True:
                not_parseable.append(x)
            else:
                for y in x.transactions:
                    transaction_list.append(y)
        else:
            link_list.append(x)
    df23 = pd.DataFrame.from_records(s.to_dict() for s in transaction_list)
    df23.to_csv('full_pull.pkl')
    pickle.dump(transaction_data, open('bulk_data.pkl', 'wb'))
    pickle.dump(not_parseable, open('computer_vision.pkl', 'wb'))


#document = './not_parse_able/9110456.pdf'
#print(parse_html(document))

#bulkHouseCollection()




