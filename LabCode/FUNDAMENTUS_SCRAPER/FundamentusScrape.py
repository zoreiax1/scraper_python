# -*- coding: utf-8 -*-
################# CABEÇALHO#################
"""
Created on Fri Oct 22 10:41:32 2021

@author: Deni

Scraper do site https://www.fundamentus.com.br
"""

################# DOCUMENTAÇÃO#################
'''
https://selenium-python.readthedocs.io/installation.html#introduction
pip install selenium

Selenium requires a driver to interface with the chosen browser. Firefox, for example, requires geckodriver, which needs to be installed before the below examples can be run. Make sure it’s in your PATH, e. g., place it in /usr/bin or /usr/local/bin.

Failure to observe this step will give you an error selenium.common.exceptions.WebDriverException: Message: ‘geckodriver’ executable needs to be in PATH.

Other supported browsers will have their own drivers available. Links to some of the more popular browser drivers follow.

Chrome: 	https://sites.google.com/chromium.org/driver/
Edge:   	https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/
Firefox: 	https://github.com/mozilla/geckodriver/releases
Safari: 	https://webkit.org/blog/6900/webdriver-support-in-safari-10/

'''

URLroot = 'https://www.fundamentus.com.br'
driverPath = r'C:\BrowserDrivers'

import time
import pathlib
import os
import shutil
import pandas as pd
from zipfile import ZipFile


from selenium import webdriver #pip install selenium
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service


from PIL import Image
from matplotlib import pyplot as plt
from IPython import get_ipython
get_ipython().run_line_magic('matplotlib', 'inline')

global tmpDataDownloadDir
global ZIPDataDownloadDir
global DataDir

tmpDataDownloadDir = f'{pathlib.Path(__file__).parent.absolute()}\\DATA_FILES\\tmp'
ZIPDataDownloadDir = f'{pathlib.Path(__file__).parent.absolute()}\\DATA_FILES\\zip'
DataDir = f'{pathlib.Path(__file__).parent.absolute()}\\DATA_FILES'

def Start():
    global tmpDataDownloadDir
    
    # Path to your GeckoDriver executable
    gecko_driver_path = "/BrowserDrivers/geckodriver.exe"

    profile = webdriver.FirefoxProfile()
    profile.set_preference("browser.download.folderList",2)
    profile.set_preference("browser.download.manager.showWhenStarting", False)
    profile.set_preference("browser.download.dir",tmpDataDownloadDir)

    # Text File (.txt) – text/plain
    # PDF File (.pdf) – application/pdf
    # CSV File (.csv) – text/csv or “application/csv”
    # MS Excel File (.xlsx) – application/vnd.openxmlformats-officedocument.spreadsheetml.sheet or application/vnd.ms-excel
    # MS word File (.docx) – application/vnd.openxmlformats-officedocument.wordprocessingml.document
    # Zip file (.zip) – application/zip
    profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/octet-stream,application/vnd.ms-excel,application/x-gzip,application/zip")
    
    # Set up the service with the GeckoDriver path
    service = Service(executable_path=gecko_driver_path)

    driver = webdriver.Firefox(firefox_profile =profile)
    return driver


def Kill(driver):
    driver.close()

def GetPaperBalancePageURL(tick):
    return f'https://www.fundamentus.com.br/balancos.php?papel={tick}&tipo=1'


def renameCaptcha(CAPTCHAstr):
    import os
    os.rename('CAPTCHAS/image.png',f'CAPTCHAS/{CAPTCHAstr}.png')


def renameZip(ticker):
    import os
    global tmpDataDownloadDir
    filelist = [ f for f in os.listdir(tmpDataDownloadDir) if f.endswith(".zip") ]
    if (len(filelist)==1):
        absFN  = f'{tmpDataDownloadDir}\{filelist[0]}'
        ansNFN = f'{tmpDataDownloadDir}\{ticker}.zip'
        os.rename(absFN,ansNFN)
        return f'{ticker}.zip'

def clearDataTMP():
    global tmpDataDownloadDir
    filelist = [ f for f in os.listdir(tmpDataDownloadDir) if f.endswith(".zip") ]
    print(f'clearing {filelist}')
    for f in filelist:
        os.remove(os.path.join(tmpDataDownloadDir, f))


def moveZip(fn):
    global tmpDataDownloadDir
    global ZIPDataDownloadDir
    absFN = f'{tmpDataDownloadDir}\\{fn}'
    absNFFN = f'{ZIPDataDownloadDir}\\{fn}'
    shutil.move(absFN, absNFFN)


def ExtractZip(file, ticker):
    global DataDir, ZIPDataDownloadDir
    fpath = f'{ZIPDataDownloadDir}\\{file}'
    # open the zip file in read mode
    with ZipFile(fpath, 'r') as zip:
        # list all the contents of the zip file
        # zip.printdir()

        # extract all files
        # print('extraction...')
        try:
            os.remove(f'{DataDir}\\{ticker}.xls')
        except:
            pass
        try:
            os.remove(f'{DataDir}\\balanco.xls')
        except:
            pass

        zip.extractall(DataDir)

        os.rename(f'{DataDir}\\balanco.xls',f'{DataDir}\\{ticker}.xls')
        # print('Done!')

def GetPaperFile(tickers, driver):
    global tmpDataDownloadDir
    for ticker in tickers:
        DOWNLOAD_FAILED = True
        while DOWNLOAD_FAILED:
            driver.get(GetPaperBalancePageURL(ticker))
            assert "FUNDAMENTUS" in driver.title

            print(f'Solve the CAPTCHA for {ticker}...-------------------------')
            PrintCaptcha(driver)
            try:
                CAPTCHAstr = input()
                clearDataTMP()
            except:
                break
            renameCaptcha(CAPTCHAstr)
            print(f'Solution entered: [{CAPTCHAstr}]')

            elem = driver.find_element(By.NAME, "codigo_captcha")
            elem.clear()
            elem.send_keys(CAPTCHAstr)
            elem.send_keys(Keys.RETURN)
            WebDriverWait(driver, 2)
            time.sleep(5)
            fn = renameZip(ticker)
            time.sleep(2)
            try:
                moveZip(fn)
                DOWNLOAD_FAILED = False
            except:
                DOWNLOAD_FAILED = True
                print("Download failed (Captcha wrong?)... Try again")
                continue
            ExtractZip(fn, ticker)

            print(f'saved to {fn}')




def PrintCaptcha(driver):

    # get element
    element = driver.find_element(By.CLASS_NAME, "captcha")
    # get rect
    location = element.location
    size = element.size

    print(driver.save_screenshot("CAPTCHAS/WorkArea/image.png"))

    x = location['x']
    y = location['y']
    width = location['x']+size['width']
    height = location['y']+size['height']

    im = Image.open('CAPTCHAS/WorkArea/image.png')
    im = im.crop((int(x), int(y), int(width), int(height)))
    im.save('CAPTCHAS/image.png')
    plt.imshow(im)
    plt.show()


def LoadTickerInfoTable():
    Tickers_Info_Table_File_Path = r'..\MARKET_DATABASE\Consult\TICKERS.xlsx'
    try:
        print(f'Loading [{Tickers_Info_Table_File_Path}]')
        TickerInfoTable = pd.read_excel(Tickers_Info_Table_File_Path,sheet_name='DATA')
        return TickerInfoTable.copy()
    except:
        print(f'Error Loading [{Tickers_Info_Table_File_Path}]')




tickers = [
# 'SAPR4',
# 'EZTC3',
# 'LREN3',
# 'BRSR6',
# 'BBSE3',
# 'CXSE3',
# 'FLRY3',
# 'HYPE3',
# 'SULA11',
# 'CRFB3',
# 'CYRE3',
# 'AESB3',
'PETR4'
    ]
# tickerTable = LoadTickerInfoTable()
# tickers = tickerTable['TICKER']

print(tickers)
input()
driver = Start()
GetPaperFile(tickers, driver)
# PrintCaptcha(driver)
Kill(driver)











