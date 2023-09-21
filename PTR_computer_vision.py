import cv2
from img2table import document,ocr
from Senate import senatePTREntry, transaction
from pdf2image import convert_from_path
from img2table.document import Image, PDF
from img2table.ocr.tesseract import TesseractOCR
import pytesseract
from pytesseract import Output
from PIL import Image as im
import numpy as np
import pandas as pd
def determine_orientation(imgs:list[im.Image]):
    bins = [0,0,0,0]
    for x in imgs:
        #pil_image= pil_image.transpose(im.ROTATE_90)
        open_cv_image = np.array(x.convert('RGB'))
    # Convert RGB to BGR
        open_cv_image = open_cv_image[:, :, ::-1].copy()
        rgb = cv2.cvtColor(open_cv_image,cv2.COLOR_RGB2BGR)
        results = pytesseract.image_to_osd(rgb,output_type=Output.DICT)
        rotation = int(results["rotate"]/90 )
        bins[rotation] = bins[rotation] + 1
        max_val = max(bins)
        idx_max = bins.index(max_val)
        idx_max = idx_max * 90
    return idx_max


def alter_orientation(imgs:list[im.Image], orientation):
    if orientation == 0:
        return imgs
    switcher = {
        '90':im.ROTATE_90,
        '180':im.ROTATE_180,
        '270':im.ROTATE_270
    }
    new_orientation = switcher.get(str(orientation))
    new_img_list = []
    for x in imgs:
        new_img_list.append(x.transpose(new_orientation))
    return new_img_list


def save_images(imgs):
    for x in range(len(imgs)):
        pil_image = imgs[x]
        open_cv_image = np.array(pil_image.convert('RGB'))
    # Convert RGB to BGR
        open_cv_image = open_cv_image[:, :, ::-1].copy()
        rgb = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2BGR)
        cv2.imwrite('temp_images/page'+str(x)+'.jpg', rgb)
    return len(imgs)