# -*- coding: utf-8 -*-
"""
Created on Sun Oct 31 12:22:06 2021

@author: Deni
Log utility
"""
import pandas as pd
import datetime as dt

def LOG(msg, echo=True):
    
    logfile = 'LOG.xlsx'
    if(echo):
        print(msg)

    return 0
    try:
        log = pd.read_excel(logfile, index_col=0)
    except:
        log = pd.DataFrame(columns=['ts', 'msg'], data=["_", "_"])

    ts = dt.datetime.now()
    line = pd.DataFrame(columns=['ts', 'msg'], data=[[ts, msg]])
    

    if(not line.empty and not line.isna().all().all()):
        pd.concat([log,line], axis=0, join='outer', ignore_index=False, keys=None)
        log.to_excel(logfile)