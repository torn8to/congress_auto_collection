import pickle

import Senate
from Senate import run_senate_collection
#run_senate_collection()
from House import housePTRentry
import House

#entry = housePTRentry(name='Rohit Khanna',link=None,representative='Rohit Khanna')
#%%
#entry.parse_mail_in(None, pdf_location='./not_parse_able/9110456.pdf')

from selenium import webdriver
from Senate import parse_html
from selenium.webdriver.common.by import By


if __name__ == '__main__':
# pickle.dump(run_senate_collection(), open('senate_transactions1.pkl','wb'))
    file = open('place_holder.pkl', 'rb')
    data = pickle.load(file)
    file.close()
# %%
    driver = webdriver.Chrome()
    line_item:Senate.senatePTREntry = data[13][7]
    driver.get(line_item.link)
    try:
        driver.find_element(by=By.ID, value="errorMessage")
        driver.find_element(by=By.ID, value="agree_statement").click()
    except:
        print("failed")
    driver.get(line_item.link)

    page_content = driver.page_source
    parse_html(page_content,line_item)


