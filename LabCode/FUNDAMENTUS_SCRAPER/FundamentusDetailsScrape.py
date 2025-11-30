# -*- coding: utf-8 -*-
"""
Created on Sat Oct 30 18:10:14 2021

@author: Deni
Fundamentus Details Scrape
"""


############################################################
from selenium import webdriver #pip install selenium
# from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By


# from urllib.request import urlopen
from bs4 import BeautifulSoup #pip install beautifulsoup4
import requests #pip install --upgrade requests

import pandas as pd
import time
import pathlib
import datetime as dt
import matplotlib.pyplot as plt

from Log import LOG

############################################################



URLTemplate = 'https://www.fundamentus.com.br/detalhes.php?papel={ticker}'

ticker = 'WXYZ4'

driverPath = r'C:\BrowserDrivers'

tmpDataDownloadDir = f'{pathlib.Path(__file__).parent.absolute()}\\DATA_FILES\\tmp'
ZIPDataDownloadDir = f'{pathlib.Path(__file__).parent.absolute()}\\DATA_FILES\\zip'
DataDir = f'{pathlib.Path(__file__).parent.absolute()}\\DATA_FILES'
DownloadDir = '..\\MARKET_DATABASE\\FUNDAMENTUS_DB\\Details'

############################################################


def Start():
    global tmpDataDownloadDir
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

    driver = webdriver.Firefox(firefox_profile =profile)
    return driver


def Kill(driver):
    driver.close()


def GetDetailsPageURL(ticker):
    return f'https://www.fundamentus.com.br/detalhes.php?papel={ticker}'

def GetCompanyMetrics(tickers, driver):

    for ticker in tickers:
        driver.get(GetDetailsPageURL(ticker))
        assert "FUNDAMENTUS" in driver.title

        elem_Cell_title = driver.find_element(By.XPATH, "// span[contains(text(),'P/L')]")
        # elem_Cell_Content = driver.find_element(By.XPATH, "// td[contains(text(),'P/L')]")

        # elem.clear()
        # elem.send_keys(CAPTCHAstr)
        # elem.send_keys(Keys.RETURN)
        WebDriverWait(driver, 2)
        time.sleep(5)


        print(f'Text: {elem_Cell_title.id}')


def LoadTickerInfoTable():
    Tickers_Info_Table_File_Path = r'..\MARKET_DATABASE\Consult\TICKERS.xlsx'
    try:
        print(f'Loading [{Tickers_Info_Table_File_Path}]')
        TickerInfoTable = pd.read_excel(Tickers_Info_Table_File_Path,sheet_name='DATA')
        return TickerInfoTable.copy()
    except:
        print(f'Error Loading [{Tickers_Info_Table_File_Path}]')


def getDetailsData(Tickers):
    headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0", "Accept-Encoding":"gzip, deflate", "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "DNT":"1","Connection":"close", "Upgrade-Insecure-Requests":"1"}
    DataSet = []
    tcount=0
    total = len(Tickers)
    for ticker in Tickers:
        skipTicker=False
        URL = GetDetailsPageURL(ticker)
        tcount+=1
        LOG(f'{ticker} - {tcount}/{total} ({round(tcount*100/total,2)}%)')
        err=True
        while (err):
            try:
                r = requests.get(URL, headers=headers)#, proxies=proxies)
                err=False
            except:
                print(f"Request error: {ticker} {URL}")
                pass
        content = r.content
        soup = BeautifulSoup(content, features="lxml")
        if(soup.text.find('Nenhum papel encontrado')>=0):
            LOG(f'\t{ticker} not found... skipping')
            continue
        # print(soup)
        alls = []
        DataTable = pd.DataFrame(columns=['label', 'data'])
        # print("Start Soup---------------")
        # print(soup.find_all('tr'))
        # print("End   Soup---------------")
        for tr in soup.find_all('tr'):
            # print('-----------------------')
            pair=0
            
            if(skipTicker):
                skipTicker=False
                continue
            for td in tr.find_all('td'):
                try:
                    if(td['class'][0]=='label'):

                        label = td.find('span', attrs={'class':'txt'}).text
                    elif(td['class'][0]=='data'):
                        try:
                            # print(f'{td}')
                            data = td.find('span', attrs={'class':'txt'}).text
                            
                        except:
                            label=''
                            data=''
                            continue
                            
                        # DataTable = DataTable.append(pd.DataFrame(data=[[label, data]], columns=DataTable.columns)).copy()
                        DataTable = pd.concat([DataTable, pd.DataFrame(data=[[label, data]], columns=DataTable.columns)]).copy()
                    else:

                        continue
                except:
                    LOG(f'\t {ticker} page failed on scraping method... skipping')
                    skipTicker = True
                    break
        DataTable.index = range(0, len(DataTable))
        RL12m = True
        RL3m = True
        EBIT12m = True
        EBIT3m = True
        LL12m = True
        LL3m = True
        RIF12m = True
        RIF3m = True
        RS12m = True
        RS3m = True
        R12m = True
        R3m = True
        VA12m = True
        VA3m = True
        FFO12m = True
        FFO3m = True
        RD12m = True
        RD3m = True

        for i in range(0, len(DataTable)):
            if((DataTable['label'].iloc[i]!='Setor') and (DataTable['label'].iloc[i]!='Subsetor')):
                DataTable.loc[i, 'data'] = DataTable['data'].iloc[i].replace('\n', '')
                DataTable.loc[i, 'data'] = DataTable['data'].iloc[i].replace('.', '')
                DataTable.loc[i, 'data'] = DataTable['data'].iloc[i].replace(',', '.')

            if(DataTable['data'].iloc[i].find('%')>=0):
                DataTable.loc[i, 'data'] = DataTable['data'].iloc[i][0:-1]

            try:
                DataTable.loc[i, 'data'] = float(DataTable['data'].iloc[i])
            except:
                pass
            try:
                if ((DataTable['label'].iloc[i]=='Data últ cot') or (DataTable['label'].iloc[i]=='Últ balanço processado')):
                    DataTable.loc[i, 'data'] = dt.datetime.strptime(DataTable['data'].iloc[i], '%d/%m/%Y')
                    # print(DataTable['data'].iloc[i].strftime('%Y %b %d'))
            except:
                LOG(f'\t{ticker} date format [{DataTable["data"].iloc[i]}] not recognized... skipping')
                skipTicker = True
                break
            if ((DataTable['label'].iloc[i]=='Receita Líquida') and RL12m):
                DataTable.loc[i, 'data'] ='Receita Líquida 12m'
                RL12m = False

            if ((DataTable['label'].iloc[i]=='Receita Líquida') and RL3m):
                DataTable.loc[i, 'data'] ='Receita Líquida 3m'
                RL3m = False

            if ((DataTable['label'].iloc[i]=='EBIT') and EBIT12m):
                DataTable.loc[i, 'data'] ='EBIT 12m'
                EBIT12m = False

            if ((DataTable['label'].iloc[i]=='EBIT') and EBIT3m):
                DataTable.loc[i, 'data'] ='EBIT 3m'
                EBIT3m = False

            if ((DataTable['label'].iloc[i]=='Lucro Líquido') and LL12m):
                DataTable.loc[i, 'data'] ='Lucro Líquido 12m'
                LL12m = False

            if ((DataTable['label'].iloc[i]=='Lucro Líquido') and LL3m):
                DataTable.loc[i, 'data'] ='Lucro Líquido 3m'
                LL3m = False

            if ((DataTable['label'].iloc[i]=='Result Int Financ') and RIF12m):
                DataTable.loc[i, 'data'] ='Result Int Financ 12m'
                RIF12m = False

            if ((DataTable['label'].iloc[i]=='Result Int Financ') and RIF3m):
                DataTable.loc[i, 'data'] ='Result Int Financ 3m'
                RIF3m = False

            if ((DataTable['label'].iloc[i]=='Rec Serviços') and RS12m):
                DataTable.loc[i, 'data'] ='Rec Serviço 12m'
                RS12m = False

            if ((DataTable['label'].iloc[i]=='Rec Serviços') and RS3m):
                DataTable.loc[i, 'data'] ='Rec Serviço 3m'
                RS3m = False

            if ((DataTable['label'].iloc[i]=='Receita') and R12m):
                DataTable.loc[i, 'data'] ='Receita 12m'
                R12m = False

            if ((DataTable['label'].iloc[i]=='Receita') and R3m):
                DataTable.loc[i, 'data'] ='Receita 3m'
                R3m = False

            if ((DataTable['label'].iloc[i]=='Venda de ativos') and VA12m):
                DataTable.loc[i, 'data'] ='Venda de ativos 12m'
                VA12m = False

            if ((DataTable['label'].iloc[i]=='Venda de ativos') and VA3m):
                DataTable.loc[i, 'data'] ='Venda de ativos 3m'
                VA3m = False

            if ((DataTable['label'].iloc[i]=='FFO') and FFO12m):
                DataTable.loc[i, 'data'] ='FFO 12m'
                FFO12m = False

            if ((DataTable['label'].iloc[i]=='FFO') and FFO3m):
                DataTable.loc[i, 'data'] ='FFO 3m'
                FFO3m = False

            if ((DataTable['label'].iloc[i]=='Rend. Distribuído') and RD12m):
                DataTable.loc[i, 'data'] ='Rend. Distribuído 12m'
                RD12m = False

            if ((DataTable['label'].iloc[i]=='Rend. Distribuído') and RD3m):
                DataTable.loc[i, 'data'] ='Rend. Distribuído 3m'
                RD3m = False



        # print(URL)
        # print(DataTable)
        
        # break
        if(skipTicker):
            skipTicker = False
            continue

        duplicatedLabelTest = DataTable[DataTable.duplicated(keep=False, subset=['label', 'data'])]
        if(len(duplicatedLabelTest)>0):
            LOG(f'Dulpicated columns in {ticker} {duplicatedLabelTest}')

        filename = f'{ticker}'
        DataTable.to_excel(f'{DownloadDir}\\{filename}.xlsx', sheet_name='DETAILS')
        DataSet.append(DataTable)
    return DataSet



# tickers = [

# 'PETR4',
# 'MGLU3',
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

#     ]

tickerTable = LoadTickerInfoTable()
tickers = tickerTable['TICKER']


dataTickers = getDetailsData(tickers)
# tn=[]
# PE = []
# ROA = []
# print(dataTickers[0])
# for df in dataTickers:
#     tn.append(df[df['label']=='Papel']['data'].iloc[0])
#     PE.append(df[df['label']=='P/L']['data'].iloc[0])
#     ROA.append(df[df['label']=='EBIT / Ativo']['data'].iloc[0])

# print(tn)
# print(PE)
# print(ROA)


# plt.scatter(1/PE, ROA, s=5, alpha=0.5)


# for i in range(0,len(tn)):
#     t = tn[i]
#     x = PE[i]
#     y = ROA[i]

#     plt.annotate(f'{t}' , xy=(x,y), textcoords='data', fontsize=8)
# plt.show()

# driver = Start()
# GetCompanyMetrics(tickers, driver)
# # PrintCaptcha(driver)
# Kill(driver)




