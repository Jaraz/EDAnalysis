# -*- coding: utf-8 -*-
from __future__ import division
from Quandl import Quandl
from matplotlib import pyplot
import pandas
import numpy

#quadl authentication token
auth_tok = "EuSxuE2sgxd21EWpW-J9"

#edFuture class encapsulates pulling data / building graphs / realized vol calc + correlations
class edFuture:
    def __init__(self,startDate):
        #create dictionary mapping ED contract to #, 1st, 2nd, 3rd, etc
        d = {1:"EDH2014", 2:"EDM2014", 3:"EDU2014", 4:"EDZ2014",
             5:"EDH2015", 6:"EDM2015", 7:"EDU2015", 8:"EDZ2015",
             9:"EDH2016", 10:"EDM2016", 11:"EDU2016", 12:"EDZ2016",
             13:"EDH2017", 14:"EDM2017", 15:"EDU2017", 16:"EDZ2017",
             17:"EDH2018", 18:"EDM2018", 19:"EDU2018", 20:"EDZ2018",
             21:"EDH2019", 22:"EDM2019", 23:"EDU2019", 24:"EDZ2019",
             25:"EDH2020", 26:"EDM2020", 27:"EDU2020", 28:"EDZ2020"}
            
        self.dates = {1:'2014-03-19',2:'2014-06-18',3:'2014-09-17',4:'2014-12-17',
                      5:'2015-03-18',6:'2015-06-17',7:'2015-09-16',8:'2015-12-16',
                      9:'2016-03-16',10:'2016-06-15',11:'2016-09-21',12:'2016-12-21',
                      13:'2017-03-15',14:'2017-06-21',15:'2017-09-20',16:'2017-12-20',
                      17:'2018-03-21',18:'2018-06-20',19:'2018-09-19',20:'2018-12-19',
                      21:'2019-03-20',22:'2019-06-19',23:'2019-09-18',24:'2019-12-18',
                      25:'2020-03-18',26:'2020-06-17',27:'2020-09-16',28:'2020-12-16'}
        self.startDate = startDate
        self.edDict = dict(d)

        ed1 = Quandl.get("CME/EDH2020", trim_start = self.startDate, authtoken = auth_tok)
        self.edRates = 100 - pandas.DataFrame(ed1["Settle"])
        self.edRates.columns = ["EDH2020"] 
        
        self.edVolume = pandas.DataFrame(ed1["Volume"])
        self.edVolume.columns = ["EDH2020"] 
        
        self.edOI = pandas.DataFrame(ed1["Open Interest"])
        self.edOI.columns = ["EDH2020"] 
   
    #load next 24 contracts from 2013 - need to add automatic logic based on startdate

    def loadAll(self):
        for i in range(4,29):
            label = "CME/" + self.edDict[i]
            temp = Quandl.get(label, trim_start = self.startDate, authtoken = auth_tok)
            self.edRates[self.edDict[i]] = 100 - temp["Settle"]
            self.edVolume[self.edDict[i]] = temp["Volume"]
            self.edOI[self.edDict[i]] = temp["Open Interest"]
            
        #issues with the data (even though its from the cme) - manual fix
        self.edRates["EDZ2017"]["2014-02-24"] = 3
            
    #bp/ann realized vol / no mean adj right now // Retrurns 0 if not enough days in array
    def realizedVol(self, data, endDate, days):
        df = data
        #if not enough days then return 0
        if len(df[:endDate]) < days:
            return 0

        df = df[:endDate].tail(days)
        ret = df[1:days] - df.shift(1)[1:days]
        ret2 = numpy.power(ret,2)
        return numpy.sqrt(252 * numpy.sum(ret2)/(days-1))[0] * 100

    #returns a table on volume / open interest / rates / (3m/6m/12m) realized vol
    def runAnalysis(self, contract, realizedDays=30):
        df = pandas.DataFrame(self.edRates[contract])
        df.columns = ["Rates"]
        df["Volume"] = self.edVolume[contract]
        df["Open Interest"] = self.edOI[contract]
        df["Realized Vol"] = 0
        for i in range(len(df)):      #Sure there isa  vectorized way to do this, don't want to waste time  
            df["Realized Vol"][i]  = self.realizedVol(contract, df.index[i], realizedDays)
        return df

    #will run analysis (realized vol / OI /etc) // Input # of contract
    def runRealizedColors(self, contract, realizedDays=30):
        reds  = pandas.DataFrame(self.edRates[self.edDict[contract]]/4)
        greens= pandas.DataFrame(self.edRates[self.edDict[contract+4]]/4)
        blues = pandas.DataFrame(self.edRates[self.edDict[contract+8]]/4)
        
        for i in range(1,4):
            reds += self.edRates[self.edDict[contract+i]]/4
            greens   += self.edRates[self.edDict[contract+i+4]]/4
            blues += self.edRates[self.edDict[contract+i+8]]/4
        
        reds["Realized Vol"] = 0
        greens["Realized Vol"] = 0
        blues["Realized Vol"] = 0        
        
        for i in range(len(reds)):      #Sure there isa  vectorized way to do this, don't want to waste time  
            reds["Realized Vol"][i]  = self.realizedVol(reds, reds.index[i], realizedDays)
            greens["Realized Vol"][i]  = self.realizedVol(greens, greens.index[i], realizedDays)
            blues["Realized Vol"][i]  = self.realizedVol(blues, blues.index[i], realizedDays)
        
        return reds,greens,blues

    #given a starting future // return the next 3 packs // contract is first of the reds
    def returnColors(self, startContract, date):
        answer = pandas.DataFrame(index = ['Futures'])
        reds   = 0
        greens = 0
        blues  = 0
        for i in range(4):
            reds += self.edRates[self.edDict[startContract+i]][date]/4*100
            greens   += self.edRates[self.edDict[startContract+i+4]][date]/4*100
            blues += self.edRates[self.edDict[startContract+i+8]][date]/4*100
        answer['reds'] = reds
        answer['greens'] = greens
        answer['blues'] = blues
        return answer

ed = edFuture("2013-01-01")
ed.loadAll()