import pickle

import cv2

import Senate
from Senate import run_senate_collection
#run_senate_collection()

#entry = housePTRentry(name='Rohit Khanna',link=None,representative='Rohit Khanna')
#%%
#entry.parse_mail_in(None, pdf_location='./not_parse_able/9110456.pdf')

from selenium import webdriver
from Senate import parse_html
from selenium.webdriver.common.by import By
import cv2 as cv
import pickle
from House import housePTRentry
import tempfile
data = pickle.load(open('2022pol.data','rb'))
if __name__ == '__main__':
    '''
    #pickle.dump(run_senate_collection(), open('senate_transactions1.pkl','wb'))
    y = 400
    yy = 75
    img = cv.imread('./not_parse_able/generic_transaction.jpg')
    cropped_image = img[:yy]

    w = int(cropped_image.shape[1])
    h = int(cropped_image.shape[0])
    print(w)
    resize_cropped_img = cv.resize(cropped_image,(w,h),interpolation=cv.INTER_AREA)
    final_display_image = resize_cropped_img
    cv.imshow("cropped",final_display_image)
    cv.waitKey(0)
    '''

