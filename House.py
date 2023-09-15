import os
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


load_dotenv()
tesseract = EasyOCR(lang=['en'])

class housePTRentry:
    def __init__(self, name, link, representative, isPaper=True):
        self.name = name
        self.link = link
        self.representative = representative
        self.isPaper = isPaper
        self.transactions = []
        self.type = 'H'




def grab_document(year:int or str,DocID:str,tmp: tempfile.TemporaryDirectory):
     base_string = "https://disclosures-clerk.house.gov/public_disc/ptr-pdfs"
     full_string = base_string + "/" + str(year) + "/" + str(DocID) + ".pdf"
     r = requests.get(full_string)
     filename = Path(tmp.name + str(year) + str(DocID) + '.pdf')
     print(filename)
     filename.write_bytes(r.content)
     return filename



def get_type(line_item:str):
    open_bracket = line_item.index(r'[') + 1
    close_bracket = line_item.index(r']')
    category = line_item[open_bracket:close_bracket]
    print(category)
    return category

def get_name(self, line_item, type):
    pass
def get_ticker(self, line_item):
    open_bracket = line_item.index(r'(') + 1
    close_bracket = line_item.index(r')')
    category = line_item[open_bracket:close_bracket]
    return category

def get_amount(self, line_item):
    first_money = line_item.split(" ")
    val = None
    for x in first_money:
        if '$' in first_money:
            val = x
                break

        amount_type = {
            "$1,001": "$1,001-$15,000",
            "$15,001": "$15,001-$50,000",
            "$50,001": "$50,001-$100,000",
            "$100,001": "$100,001-$250,000",
            "$250,001": "$250,001-$500,000",
            "$500,001": "$500,001-$1,000,000"
        }
        amount = amount_type.get(val, lambda: "$1,001-$15,000")
        return amount


def get_account_type(line_item):
     account_time = line_item[4:6]
     if account_time == 'JT' or account_time == 'SP':
        return account_time
     return 'S'


def get_transaction_type(line_item):
        res = []
        for x in line_item.split(" "):
            if len(x) == 1:
                res.append(x)
        transaction_type = 'P'
        for x in res:
            if x.lower().find("P") > -1:
                transaction_type = "P"
                break
            elif x.lower().find("S") > -1:
                transaction_type = "S"
                break
            elif x.lower().find("E") > -1:
                transaction_type = "S"
                break
        for x in line_item.split(" "):
            if len(x) == 2:
                res.append(x)
        for x in res:
            if x.lower().find("PS") > -1:
                transaction_type = "S"
        return transaction_type


def get_transaction_date(self,line_item):
    pass

def get_report_date(self,line_item):
    pass

def parse_stock_default(house_entry:housePTRentry ,line_item):
    return transaction( house_entry,
                           get_report_date(line_item),
                           get_transaction_date(line_item),
                           house_entry.representative,
                           get_name(line_item),
                           get_type(line_item),
                           get_amount(line_item),
                           get_transaction_type(line_item),
                           get_ticker(line_item),
                           "H")


def parse_other(self,line_item):
    pass



def invalid(self):
    pass


def determine_document_type(file_location):
    soup = BeautifulSoup(open(file_location))
    body = soup.find("body")
    title = None

    try:
        p_list = body.find_all("p")
        for x in p_list:
            for z in x['style'].split():
                if 'margin-left:95.65' in z and 'P' in x.text:
                    title = True
    except:
        print("Mail in document")

    if title != None:
        return 'ClASSIC_PTR'
    else:
        return 'MAIL_IN_PTR'



def parse_html(self, file_location:str, pdf_location:str):
    data_text ="font-size:"
    soup = BeautifulSoup(open(file_location), 'html.parser')
    doc_type = self.determine_document_type(file_location)
    switcher ={
             'ClASSIC_PTR': self.parse_classic,
                "MAIL_IN_PTR": self.parse_mail_in,
            }
    func = switcher.get(doc_type)
    return func(file_location, pdf_location)


def parse_classic(file_location:str, pdf_location:str):
        soup = BeautifulSoup(open(file_location), 'html.parser')
        tables = soup.find('tbody')
        table_rows = soup.find_all('tr')
        buffer = table_rows
        for x in table_rows:
        #print(table_rows[x].text)
         if ":" in x.getText():
                table_rows.remove(x)
        print(len(buffer))
        print(len(table_rows))
        l = []
        for x in buffer:
            l.append(x.text)
        result = []
        [result.append(x) for x in l if "D:" not in x]
        for x in result:
            print(x)
        result.pop(0)

def parse_mail_in(file_location, pdf_location):
    pass
    '''
        Image = None
        with pikepdf.Pdf.open(pdf_location, allow_overwriting_input=True) as my_pdf:
            for page in my_pdf.pages:
                page.rotate(angle=270, relative=False)

            my_pdf.save(pdf_location)
            my_pdf.save(my_pdf.filename)

            image = convert_from_path('./not_parse_able/' + my_pdf.filename, dpi=400,poppler_path='')
            first_page = image[0]
            tess = pytesseract.image_to_string(first_page)
            print(tess)
            if "please see attached" in tess:
                return parse_spread_sheet(image)
    '''

def parse_spread_sheet(images,):
    for x in images:
        x.convert('RGB')
            cv_image = cv.cvtColor(np.array(x))
            t = tempfile.NamedTemporaryFile()
            cv.imwrite(t)
            doc = Image(t)
            extracted_tables = Image.extract_tables(ocr=tesseract,
                                 implicit_rows=False,
                                 borderless_tables=False,
                                 min_confidence=50)






    def parse_string(self,line_item: str):
        type = self.get_type(line_item)
        switcher = {
        'ST': self.parse_stock,
        }
        func = switcher.get(type, lambda: self.invalid)
        return func(line_item)

    def get_mail_in_spreadsheet(self, Images):
        list_of_transactions = []
        for x in Images:
            pass


    def get_ticker(company_name):
        yfinance = "https://query2.finance.yahoo.com/v1/finance/search"
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
        params = {"q": company_name, "quotes_count": 1, "country": "United States"}

        res = requests.get(url=yfinance, params=params, headers={'User-Agent': user_agent})
        data = res.json()

        company_code = data['quotes'][0]['symbol']
        return company_code

def runHouseCollection():

    ptr_temp_directory = tempfile.TemporaryDirectory()
    data = pd.DataFrame()
    with tempfile.TemporaryDirectory() as temp:
        '''
        avaliable_years = ['2020','2021','2022','2023']
        for year in avaliable_years:
        '''

        asd = requests.get('https://disclosures-clerk.house.gov/public_disc/financial-pdfs/2023FD.ZIP', stream=True)
        if asd.ok:
            z = zipfile.ZipFile(io.BytesIO(asd.content))
            z.extractall(temp)

        data = pd.read_csv(temp + '/2023FD.txt', sep="\t", header=0)
        print(data.keys())
        time_filtering =  data[data['ReportDate']]
        document_type_filtering = data[data['FilingType'] == 'P']


    for x in range(20):
        doc_id = document_type_filtering.iloc[x]['DocID']
        year = document_type_filtering.iloc[x]['Year']
        filename = grab_document(year, doc_id, ptr_temp_directory)
        doc = aw.Document(filename.__str__())
        doc.save('./dump_directory/file' + str(x) + '.html')
        parse_html('./dump_directory/file' + str(x) + '.html')


#document = './not_parse_able/9110456.pdf'
#print(parse_html(document))


#runHouseCollection()