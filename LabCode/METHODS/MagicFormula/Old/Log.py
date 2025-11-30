# -*- coding: utf-8 -*-
"""
Created on Sun Oct 31 12:22:06 2021

@author: Deni
Log utility
"""
import pandas as pd
import datetime as dt

def LOG(msg, echo=True):
    logfile = 'LOG.xls'
    if(echo):
        print(msg)
    try:
        log = pd.read_excel(logfile, index_col=0)
    except:
        log = pd.DataFrame(columns=['ts', 'msg'])

    ts = dt.datetime.now()
    line = pd.DataFrame(columns=['ts', 'msg'], data=[[ts, msg]])
    log = log.append(line)
    log.to_excel(logfile)