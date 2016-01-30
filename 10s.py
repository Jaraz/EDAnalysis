# -*- coding: utf-8 -*-
from __future__ import division
from fredapi import Fred
import numpy
import scipy
import pandas as pd
from matplotlib import pyplot
from scipy import interpolate
from scipy import optimize
import statsmodels.formula.api as smf
import statsmodels.api as sm

localDir = 'C:\Users\jaycw_000\Documents\GitHub\EDAnalysis\srvixclose.csv'
localDir2 = 'C:\Users\jaycw_000\Documents\GitHub\EDAnalysis\sp500.xls'
fred = Fred(api_key='ba6be791f155502772efcac065904210')

startDate = '1990-01-01'
endDate = '2016-01-07'

def pullData(startDate, endDate):
    
    df = {}
    df["sp"] = fred.get_series('sp500', observation_start = startDate, observation_end = endDate)
    df["tens"] = fred.get_series('DGS10', observation_start = startDate, observation_end = endDate)
    df["cpi"] = fred.get_series('CPIAUCSL', observation_start = startDate, observation_end = endDate)
    df["medCPI"] = fred.get_series('MEDCPIM157SFRBCLE', observation_start = startDate, observation_end = endDate)
    df["gdp"] = fred.get_series('GDP', observation_start = startDate, observation_end = endDate)
    df["eur"] = fred.get_series('DEXUSEU', observation_start = startDate, observation_end = endDate)
    df["usBasket"] = fred.get_series('DTWEXM', observation_start = startDate, observation_end = endDate)
    df["tips"] = fred.get_series('DFII10', observation_start = startDate, observation_end = endDate)
    df["ffs"] = fred.get_series('DFF', observation_start = startDate, observation_end = endDate)
    df["debt"] = fred.get_series('GFDEBTN', observation_start = startDate, observation_end = endDate)
    df["debtGDP"] = fred.get_series('GFDEGDQ188S', observation_start = startDate, observation_end = endDate)
    df = pd.DataFrame(df)
    
#load csv files
    test = pd.read_csv(localDir,index_col=0,header=None,parse_dates=[0])
    df['vol'] = test

    test = pd.read_excel(localDir2,index_col=0,parse_dates=[0])
    df['div']=test['Dividend Yield']*100 
    df['annSP']=test['S&P 500']
    df['earnSP']=test['Earnings Yield']*100 
    

    return df

def plot2(var1, var2, df, start=None, end=None):
    fig, ax1 = pyplot.subplots()
    ax1.plot(df.index, df[var1])
    ax1.set_ylabel(var1)
    
    ax2 = ax1.twinx()
    ax2.plot(df.index, df[var2], c='red')
    pyplot.show()

def runRegression(depVar, indVar, inputDF, start=None, end=None):
    if start is None:
        start = inputDF.index[0]
    if end is None:
        end = inputDF.index[len(inputDF)-1]
    df = inputDF[[depVar,indVar]]
    df = df[start:end].dropna()
    lm = smf.ols(formula=depVar+'~'+indVar, data = df).fit()

    #df.plot(kind='scatter', x = indVar, y=depVar, c=df.index,cmap=pyplot.cm.viridis)
    pyplot.scatter(df[indVar],df[depVar],c=df.index,cmap=pyplot.cm.viridis)
    pyplot.colorbar()
    pyplot.plot(df[indVar], lm.params[1]*df[indVar] + lm.params[0],c="red",linewidth=2)

    print lm.rsquared
    return lm

#just starting
def run2Regression(depVar, indVar1, indVar2, inputDF, start=None, end=None):
    if start is None:
        start = inputDF.index[0]
    if end is None:
        end = inputDF.index[len(inputDF)-1]
        
    df2 = inputDF[[depVar,indVar1,indVar2]].dropna()
    df = df2[start:end]

    lm = smf.ols(formula=depVar+'~'+indVar1 +"+"+indVar2, data = df).fit()

    x_new = inputDF[[depVar,indVar1,indVar2]].interpolate().dropna()
    preds = lm.predict(x_new[[indVar1,indVar2]])
    #print x_new.index, len(inputDF[depVar].interpolate().dropna())
    #pyplot.plot(x_new.index,inputDF[depVar].interpolate().dropna())
    pyplot.plot(inputDF[depVar].index,inputDF[depVar])
    pyplot.plot(x_new.index,preds,c='red',linewidth=2)
    
    print lm.rsquared
    return lm

def run3Regression(depVar, indVar1, indVar2, indVar3, inputDF, start=None, end=None):
    if start is None:
        start = inputDF.index[0]
    if end is None:
        end = inputDF.index[len(inputDF)-1]
        
    df2 = inputDF[[depVar,indVar1,indVar2,indVar3]].dropna()
    df = df2[start:end]

    lm = smf.ols(formula=depVar+'~'+indVar1 +"+"+indVar2+"+"+indVar3, data = df).fit()

    x_new = inputDF[[depVar,indVar1,indVar2,indVar3]].interpolate().dropna()
    preds = lm.predict(x_new[[indVar1,indVar2,indVar3]])
    pyplot.plot(x_new.index,inputDF[depVar].interpolate().dropna())
    pyplot.plot(x_new.index,preds,c='red',linewidth=2)
    
    print lm.rsquared
    return lm

#df = pullData(startDate,endDate)