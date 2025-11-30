# -*- coding: utf-8 -*-
"""
Created on Sat Oct 30 15:46:39 2021

@author: Deni
process Fundamentus files using the magic formula from "The little book that beat the market"
"""

#############################################
import pandas as pd
import datetime as dt
import os
from tqdm import tqdm#pip install tqdm
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import random as rd

from Log import LOG
#############################################

global L, H, m #Final image size
m = 5
L = 8*m
H = 6*m


RAW_FUNDAMENTUS_BALANCES_FOLDER = '..\\..\\MARKET_DATABASE\\FUNDAMENTUS_DB'
RAW_FUNDAMENTUS_DETAILS_FOLDER = '..\\..\\MARKET_DATABASE\\FUNDAMENTUS_DB\\Details'

Tickers_Info_Table_File_Path = '..\\..\\MARKET_DATABASE\\Consult\\Tickers.xlsx'

MAGIC_TEMP_FOLDER = 'tmp'
MAGIC_RES_FOLDER = 'Results'

TSstr = '[%Y-%m-%d.%H.%M.%S]'
TS = dt.datetime.now().strftime(TSstr)

def LoadTickerInfoTable():
    global Tickers_Info_Table_File_Path
    try:
        print(f'Loading [{Tickers_Info_Table_File_Path}]')
        TickerInfoTable = pd.read_excel(Tickers_Info_Table_File_Path,sheet_name='DATA')
        return TickerInfoTable.copy()
    except:
        print(f'Error Loading [{Tickers_Info_Table_File_Path}]')


def GetFilePaths(path):
    # path = RAW_FUNDAMENTUS_DETAILS_FOLDER
    list_of_files = []

    for root, dirs, files in os.walk(path):
    	for file in files:
    		list_of_files.append(os.path.join(root,file))
    return list_of_files


def LoadDitailsFile(path):
    try:
        DetailsData = pd.read_excel(path, sheet_name="DETAILS", index_col=0)
        
    except:
        LOG(f'Error loading {path} ', echo=False)
        return -1
    for i in range(0, len(DetailsData)):
        try:
            DetailsData.loc[i, 'data'] = float(DetailsData['data'].iloc[i])
        except:
            pass
        try:
            if ((DetailsData['label'].iloc[i]=='Data últ cot') or (DetailsData['label'].iloc[i]=='Últ balanço processado')):
                DetailsData.loc[i, 'data'] = dt.datetime.strptime(DetailsData['data'].iloc[i], '%d/%m/%Y')
                # print(DataTable['data'].iloc[i].strftime('%Y %b %d'))
        except:
            try:
                if ((DetailsData['label'].iloc[i]=='Data últ cot') or (DetailsData['label'].iloc[i]=='Últ balanço processado')):
                    if(isinstance(DetailsData['data'].iloc[i], str)):
                        DetailsData.loc[i, 'data'] = dt.datetime.strptime(DetailsData['data'].iloc[i], '%Y-%m-%d %H:%M:%S')
                    elif(isinstance(DetailsData['data'].iloc[i], dt.datetime)):
                        pass
            except:
                LOG(f'\t{path} date format [{DetailsData["data"].iloc[i]}] not recognized... skipping')
                break
    data = list(DetailsData['data'])
    columns = list(DetailsData['label'])

    df = pd.DataFrame(data = [data], columns=columns)

    return df.copy()


def GetShareTickers(Tickers):
    return Tickers[Tickers['TYPE']=='SHARE'].copy()


def PerformMagic(Tickers):
    global RAW_FUNDAMENTUS_BALANCES_FOLDER, RAW_FUNDAMENTUS_DETAILS_FOLDER, TickerDetailsData

    try:
        TickerDetailsData = pd.read_excel('DatabaseResume.xlsx', index_col=0)
        ans='x'
        while ans!='y' and ans !='n' and ans!='':
            LOG(f'Preporcessed DatabaseResume file detected. \nUse the file? (y/n):')
            ans = input()
    except:
        ans = 'n'

    if(ans=='n'):
        auxTicker = Tickers['TICKER'].iloc[0]
        path = f'{RAW_FUNDAMENTUS_DETAILS_FOLDER}\\{auxTicker}.xlsx'
        auxLine = LoadDitailsFile(path)
        TickerDetailsData = pd.DataFrame(columns=auxLine.columns)
        # print(TickerDetailsData.columns)
        for i in tqdm (range(0, len(Tickers)), desc="Loading details ..."):
            # print(len(TickerDetailsData.columns))
            ticker = Tickers['TICKER'].iloc[i]
            path = f'{RAW_FUNDAMENTUS_DETAILS_FOLDER}\\{ticker}.xlsx'
            line = LoadDitailsFile(path)
            if(isinstance(line, pd.DataFrame)):
                line.index=[len(TickerDetailsData)]
            # print(line)
            # global a1, a2
            # a1 = line.columns
            # a2 = TickerDetailsData.columns

            try:
                if(isinstance(line, pd.DataFrame)):
                    line["Data últ cot"] = pd.to_datetime(line["Data últ cot"])
                    
                    TickerDetailsData = pd.concat([TickerDetailsData, line])
                    # print(line)
                
            except:
                print("\n")
                LOG(f'Error merging {ticker}.xlsx {line}... skipping')
            # TickerDetailsData = TickerDetailsData.append(line, ignore_index=True)
            # TickerDetailsData = TickerDetailsData.append(LoadDitailsFile(path))
        # print(TickerDetailsData)
        TickerDetailsData.to_excel('DatabaseResume.xlsx')
    else:
        LOG("Utilizing cached file!")

    TickerDetailsData = TickerDetailsData.dropna(axis=0, subset=["Papel"]).copy()
    TickerDetailsData = TickerDetailsData.dropna(axis=0, subset=["P/L"]).copy()
    TickerDetailsData = TickerDetailsData.dropna(axis=0, subset=["EBIT / Ativo"]).copy()
    TickerDetailsData = TickerDetailsData.dropna(axis=0, subset=["Data últ cot"]).copy()

    ThisYear = dt.datetime.now().year
    ThisMonth = dt.datetime.now().month
    
    TickerDetailsData = TickerDetailsData[TickerDetailsData["Data últ cot"]>dt.datetime(ThisYear, ThisMonth, 1)]
    TickerDetailsData.index = range(0,len(TickerDetailsData))

    tn = TickerDetailsData["Papel"]
    PE = TickerDetailsData["P/L"]
    ROA = TickerDetailsData["EBIT / Ativo"]
    PL = TickerDetailsData["Patrim. Líq"]

    # plt.scatter(PE, ROA, s=5, alpha=0.5)
    global L, H, m
    xmin = 0
    xmax = 10
    ymin = 0
    ymax = 100
    plt.xlim(xmin, xmax)
    plt.ylim(ymin, ymax)
    plt.xlabel('P/E')
    plt.ylabel('ROA')
    plt.xticks(ticks=np.linspace(xmin, xmax, 20))
    plt.yticks(ticks=np.linspace(ymin, ymax, 20))
    plt.rc('font', size=1*m)
    plt.rc('lines', linewidth=1)

    
    plt.grid()
    Vmax = 0*(ymax-ymin)/80
    Hmax = 0*(xmax-xmin)/80

    for i in range(0,len(tn)):
        if PL[i]<0:
            t = f'{tn[i]}(-)'
        else:
            t = f'{tn[i]}(+)'
        x = PE[i]
        y = ROA[i]
        import random
        maxColor = 128.0
        r = random.randint(0,maxColor)/maxColor
        g = random.randint(0,maxColor)/maxColor
        b = random.randint(0,maxColor)/maxColor
        # hexadecimal = ["#"+''.join([random.choice('ABCDEF0123456789') for i in range(6)])]
        color = (r, g, b)
        rot = rd.randrange(-90, 90)
        if(x<xmin or x>xmax or y<ymin or y>ymax):
            continue
        plt.annotate(f'{t}' , xy=(x+rd.randrange(-1, 1)*Hmax,y+rd.randrange(-1, 1)*Vmax), textcoords='data', fontsize=2*m, color=color, alpha=0.9, rotation=rot)
        plt.scatter(PE[i], ROA[i], s=5*m, alpha=0.5, color=color)

    fname = f'{MAGIC_RES_FOLDER}\\{TS} MagicResult (PE vs ROA).svg'

    plt.gcf().set_size_inches(L, H)
    plt.savefig(fname, dpi=600)
    plt.show()

    # selection = pd.DataFrame()
    # for i in range(0, len(tickersSelected)):
    #     st = tickersSelected[i]
    #     line = TickerDetailsData[TickerDetailsData["Papel"]==st]
    #     selection = selection.append(line)

    # # print(selection['Papel'])
    # selection.sort_values(by=['P/L'], ascending=True, inplace=True)
    # # print(selection['Papel'])
    # selection['P/E score'] = list(range(0, len(selection)))
    # selection.sort_values(by=['EBIT / Ativo'], ascending=False, inplace=True)
    # # print(selection['Papel'])
    # selection['ROA score'] = list(range(0, len(selection)))
    # selection['MagicScore'] = selection['P/E score']+selection['ROA score']
    # selection.sort_values(by=['MagicScore'], ascending=True, inplace=True)
    # print(selection.loc[::,['Papel', 'P/L', 'P/E score', 'EBIT / Ativo', 'ROA score', 'MagicScore']])



    return TickerDetailsData

def AcquirersMult(Tickers):
    global RAW_FUNDAMENTUS_BALANCES_FOLDER, RAW_FUNDAMENTUS_DETAILS_FOLDER, TickerDetailsData

    try:
        TickerDetailsData = pd.read_excel('DatabaseResume.xlsx', index_col=0)
        ans='x'
        while ans!='y' and ans !='n' and ans!='':
            LOG(f'Preporcessed DatabaseResume file detected. \nUse the file? (y/n):')
            ans = input()
    except:
        ans = 'n'

    if(ans=='n'):
        auxTicker = Tickers['TICKER'].iloc[0]
        path = f'{RAW_FUNDAMENTUS_DETAILS_FOLDER}\\{auxTicker}.xlsx'
        auxLine = LoadDitailsFile(path)
        TickerDetailsData = pd.DataFrame(columns=auxLine.columns)
        # print(TickerDetailsData.columns)
        for i in tqdm (range(0, len(Tickers)), desc="Loading details ..."):
            # print(len(TickerDetailsData.columns))
            ticker = Tickers['TICKER'].iloc[i]
            path = f'{RAW_FUNDAMENTUS_DETAILS_FOLDER}\\{ticker}.xlsx'
            line = LoadDitailsFile(path)
            # global a1, a2
            # a1 = line.columns
            # a2 = TickerDetailsData.columns

            try:
                if(isinstance(line, pd.DataFrame)):
                    # TickerDetailsData = TickerDetailsData.append(line, ignore_index=True)
                    line["Data últ cot"] = pd.to_datetime(line["Data últ cot"])
                    TickerDetailsData = pd.concat([TickerDetailsData.reset_index(drop=True), line.reset_index(drop=True)], ignore_index=True)
            except:
                LOG(f'Error merging {ticker}.xlsx {line}... skipping')
            # TickerDetailsData = TickerDetailsData.append(line, ignore_index=True)
            # TickerDetailsData = TickerDetailsData.append(LoadDitailsFile(path))
        # print(TickerDetailsData)
        TickerDetailsData.to_excel('DatabaseResume.xlsx')
    else:
        LOG("Utilizing cached file!")

    TickerDetailsData["EV / EBITDA"] = pd.to_numeric(TickerDetailsData["EV / EBITDA"], errors='coerce')
    TickerDetailsData = TickerDetailsData.dropna(axis=0, subset=["Papel"]).copy()
    TickerDetailsData = TickerDetailsData.dropna(axis=0, subset=["EV / EBITDA"]).copy()
    TickerDetailsData = TickerDetailsData.dropna(axis=0, subset=["EBIT / Ativo"]).copy()
    TickerDetailsData = TickerDetailsData.dropna(axis=0, subset=["Data últ cot"]).copy()

    ThisYear = dt.datetime.now().year
    ThisMonth = dt.datetime.now().month
    
    TickerDetailsData = TickerDetailsData[TickerDetailsData["Data últ cot"]>dt.datetime(ThisYear, ThisMonth, 1)]
    TickerDetailsData.index = range(0,len(TickerDetailsData))

    tn = TickerDetailsData["Papel"]
    AM = TickerDetailsData["EV / EBITDA"]
    ROA = TickerDetailsData["EBIT / Ativo"]
    PL = TickerDetailsData["Patrim. Líq"]
    print(AM)
    # plt.scatter(PE, ROA, s=5, alpha=0.5)
    global L, H, m
    xmin = 0
    xmax = 10
    ymin = 0
    ymax = 100
    plt.xlim(xmin, xmax)
    plt.ylim(ymin, ymax)
    plt.xlabel('EV/EBITDA')
    plt.ylabel('ROA')
    plt.xticks(ticks=np.linspace(xmin, xmax, 20))
    plt.yticks(ticks=np.linspace(ymin, ymax, 20))
    plt.rc('font', size=1*m)
    plt.rc('lines', linewidth=1)

    
    plt.grid()
    Vmax = 0*(ymax-ymin)/80
    Hmax = 0*(xmax-xmin)/80

    for i in range(0,len(tn)):
        if PL[i]<0:
            t = f'{tn[i]}(-)'
        else:
            t = f'{tn[i]}(+)'
        x = AM[i]
        y = ROA[i]
        import random
        maxColor = 128.0
        r = random.randint(0,maxColor)/maxColor
        g = random.randint(0,maxColor)/maxColor
        b = random.randint(0,maxColor)/maxColor
        # hexadecimal = ["#"+''.join([random.choice('ABCDEF0123456789') for i in range(6)])]
        color = (r, g, b)
        rot = rd.randrange(-90, 90)
        if(x<xmin or x>xmax or y<ymin or y>ymax):
            continue
        plt.annotate(f'{t}' , xy=(x+rd.randrange(-1, 1)*Hmax,y+rd.randrange(-1, 1)*Vmax), textcoords='data', fontsize=2*m, color=color, alpha=0.9, rotation=rot)
        plt.scatter(AM[i], ROA[i], s=5*m, alpha=0.5, color=color)

    fname = f'{MAGIC_RES_FOLDER}\\{TS} Acquirers Multiple (EV-EBITDA vs ROA).svg'
    
    plt.gcf().set_size_inches(L, H)
    plt.savefig(fname, dpi=600)
    plt.show()



    return TickerDetailsData






tickersSelected = [
'MGEL4',

'CSNA3',

'USIM5',

'CTKA4',

'CYRE3',

'EUCA4',

    ]

Tickers = LoadTickerInfoTable()
ShareTickers = GetShareTickers(Tickers)
PerformMagic(ShareTickers)
AcquirersMult(ShareTickers)



