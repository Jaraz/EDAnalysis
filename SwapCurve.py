# -*- coding: utf-8 -*-
from __future__ import division
from fredapi import Fred
import numpy
import scipy
from matplotlib import pyplot
from scipy import interpolate
from scipy import optimize
from Quandl import Quandl
auth_tok = "EuSxuE2sgxd21EWpW-J9"
fred = Fred(api_key='ba6be791f155502772efcac065904210')

#Quick basic yield curve buidler for discounting and comaprison for convexity adj
#Couple messy assumptions // all dates .25 or .5 combined with best interpolation i could find - not too familiar with scipy interp methods
#Using Fed Reserve Swap Data - ISDAFIX 11am / only thing i could find for free at short notice

class yieldCurve:
    def __init__(self, inputDate, dataOverride=None):
        self.date = inputDate
        if dataOverride is None:        
            self.swapData = self.pullSwapData(inputDate)
        else:
            self.swapData = dataOverride
        self.curve = curveBuild(inputDate, self.swapData)
        temp = -numpy.log(self.curve[1])/self.curve[0]
        temp[0] = 0
        self.zeroCurve = interpolate.PchipInterpolator(self.curve[0], temp)

    def discFact(self, t):
        if t < 0 :
            return 1
        return numpy.exp(-self.zeroCurve(t)*t)

    #return Bumped swap data to be given to new yc obj
    def bump(self,bps):
        return self.swapData + bps/10000
    
    def returnDate(self):
        return self.date

    def fwdRate(self, start):
        return (self.discFact(start) / self.discFact(start + 0.25) - 1) / 0.25
        
    def swapRate(self, start, tenor):
        fix_per = int(tenor * 2)
        flt_per = int(tenor * 4)
    
        flt = 0
        fix = 0
    
        for i in xrange(1, fix_per+1):    
            fix = fix + 0.5 * self.discFact(start + i * 0.5)
    
        for j in xrange(1, flt_per+1):
            flt = flt + 0.25 * self.discFact(start + j * 0.25) * self.fwdRate(start + j * 0.25)
    
        return flt / fix * 10000

    #pull swap data for a date
    def pullSwapData(self, inputDate):
        swapArray = numpy.zeros(9)
        swapArray[0] = Quandl.get("FRED/USD3MTD156N", trim_start = inputDate, trim_end = inputDate, authtoken = auth_tok)["VALUE"][0]
        swapArray[1] = fred.get_series('DSWP1', observation_start=inputDate, observation_end=inputDate)[0]
        swapArray[2] = fred.get_series('DSWP2', observation_start=inputDate, observation_end=inputDate)[0]
        swapArray[3] = fred.get_series('DSWP3', observation_start=inputDate, observation_end=inputDate)[0]
        swapArray[4] = fred.get_series('DSWP4', observation_start=inputDate, observation_end=inputDate)[0]
        swapArray[5] = fred.get_series('DSWP5', observation_start=inputDate, observation_end=inputDate)[0]
        swapArray[6] = fred.get_series('DSWP7', observation_start=inputDate, observation_end=inputDate)[0]
        swapArray[7] = fred.get_series('DSWP10', observation_start=inputDate, observation_end=inputDate)[0]
        swapArray[8] = fred.get_series('DSWP30', observation_start=inputDate, observation_end=inputDate)[0]
    
        return swapArray/100
    
def curveBuild(inputDate, data):
    #data = pullSwapData(inputDate)
    curve = prepCurve()
    
    #use First deposit
    curve[1,1] = 1 / (1 + 0.25 * data[0])
    
    for j in xrange(3):
        for i in xrange(2,10):
            curve[1,i] = scipy.optimize.brentq(swapOptim, a = 0.11, b = 0.999, args = (i, 0, curve[0,i], data[i-1], curve))
    return curve
    
#assume 3m libor and periods are always whole numbers
def swapPricer(start, tenor, strike, curve):
    fix_per = int(tenor * 2)
    flt_per = int(tenor * 4)
    
    flt = 0
    fix = 0
    
    for i in xrange(1, fix_per+1):    
        fix = fix + 0.5 * curve.discFact(start + i * 0.5) * strike
    
    for j in xrange(1, flt_per+1):
        flt = flt + 0.25 * curve.discFact(start + j * 0.25) * curve.fwdRate(start + j * 0.25)
    
    return fix - flt

def swapOptim(x, n, start, tenor, strike, curve):
    curve[1,n] = x
    return swapPricer(start, tenor, strike, curve)

def swapDV01(start, tenor, curve):
    fix_per = int(tenor * 2)
    dv01 = 0
    
    for i in xrange(fix_per):    
        dv01 = dv01 + 0.5 * curve.discFact(start + i * 0.5)
    return dv01

#Initial guessfor the solver
def prepCurve():
    x = numpy.zeros((2,10))
    x.fill(0.5)
    x[0,0] = 0
    x[0,1] = 0.25
    x[0,2] = 1
    x[0,3] = 2
    x[0,4] = 3
    x[0,5] = 4
    x[0,6] = 5
    x[0,7] = 7
    x[0,8] = 10
    x[0,9] = 30

    x[1,0] = 1
    x[1,1] = 0.9993
    x[1,2] = 0.995
    x[1,3] = 0.982
    x[1,4] = 0.963
    x[1,5] = 0.942
    x[1,6] = 0.9196
    x[1,7] = 0.874
    x[1,8] = 0.806
    x[1,9] = 0.405 

    return x
   
    
def curveInterp(t, curve):
    #zero rates
    tempCurve = -numpy.log(curve[1])/curve[0]
    tempCurve[0] = 0.0000

    if t < 0:
        return 1
    elif t > 30:
        f = numpy.exp(numpy.interp(t, curve[0], numpy.log(curve[1]), right = numpy.log(curve[1,9])*t/30))
        return f
    else:
        f = interpolate.pchip_interpolate(curve[0], tempCurve, t)

    tnew = numpy.exp(-f * t)    
    return tnew

#assume 3m    
def fwdRate(start, curve):
    return (curveInterp(start, curve) / curveInterp(start + 0.25, curve) - 1) / 0.25

def swapRate(start, tenor, curve):
    fix_per = int(tenor * 2)
    flt_per = int(tenor * 4)
    
    flt = 0
    fix = 0
    
    for i in xrange(1, fix_per+1):    
        fix = fix + 0.5 * curve.discFact(start + i * 0.5)
    
    for j in xrange(1, flt_per+1):
        flt = flt + 0.25 * curve.discFact(start + j * 0.25) * curve.fwdRate(start + j * 0.25)
    
    return flt / fix * 10000
    
def plotFwd(start, tenor, curve):
    numPer = int(tenor * 4)
    
    fwds = numpy.zeros(numPer)
    dates = numpy.zeros(numPer)
    
    for i in xrange(numPer):
        dates[i] = start + 0.25 * i 
        fwds[i] = curve.fwdRate(dates[i])
    
    pyplot.plot(dates, fwds)
    return

#Assumes paying flt // inputs in bps
def fraPayoff(start, strike, curve):
    fraRate = curve.fwdRate(start)
    df = curve.discFact(start+0.25)
    return (strike/10000 - fraRate) * df / 4

#yc = yieldCurve('2015-11-30')
#dateVec = cvxBiasDates = ['2015-08-03','2015-08-04','2015-08-05','2015-08-06','2015-08-07','2015-08-10','2015-08-11','2015-08-12','2015-08-13','2015-08-14','2015-08-17','2015-08-18','2015-08-19','2015-08-20','2015-08-21','2015-08-24','2015-08-25','2015-08-26','2015-08-27','2015-08-28','2015-09-02','2015-09-03','2015-09-04','2015-09-08','2015-09-09','2015-09-10','2015-09-11','2015-09-14','2015-09-15','2015-09-16','2015-09-17','2015-09-18','2015-09-21','2015-09-22','2015-09-23','2015-09-24','2015-09-25','2015-09-28','2015-09-29','2015-09-30','2015-10-01','2015-10-02','2015-10-05','2015-10-06','2015-10-07','2015-10-08','2015-10-09','2015-10-13','2015-10-14','2015-10-15','2015-10-16','2015-10-19','2015-10-20','2015-10-21','2015-10-22','2015-10-23','2015-10-26','2015-10-27','2015-10-28','2015-10-29','2015-10-30']
#dateVec = ['2015-01-02','2015-01-05','2015-01-06','2015-01-07','2015-01-08','2015-01-09','2015-01-12','2015-01-13','2015-01-14','2015-01-15','2015-01-16','2015-01-20','2015-01-21','2015-01-22','2015-01-23','2015-01-26','2015-01-27','2015-01-28','2015-01-29','2015-01-30','2015-02-02','2015-02-03','2015-02-04','2015-02-05','2015-02-06','2015-02-09','2015-02-10','2015-02-11','2015-02-12','2015-02-13','2015-02-17','2015-02-18','2015-02-19','2015-02-20','2015-02-23','2015-02-24','2015-02-25','2015-02-26','2015-02-27','2015-03-02','2015-03-03','2015-03-04','2015-03-05','2015-03-06','2015-03-09','2015-03-10','2015-03-11','2015-03-12','2015-03-13','2015-03-16','2015-03-17','2015-03-18','2015-03-19','2015-03-20','2015-03-23','2015-03-24','2015-03-25','2015-03-26','2015-03-27','2015-03-30','2015-03-31','2015-04-01','2015-04-02','2015-04-07','2015-04-08','2015-04-09','2015-04-10','2015-04-13','2015-04-14','2015-04-15','2015-04-16','2015-04-17','2015-04-20','2015-04-21','2015-04-22','2015-04-23','2015-04-24','2015-04-27','2015-04-28','2015-04-29','2015-04-30','2015-05-01','2015-05-05','2015-05-06','2015-05-07','2015-05-08','2015-05-11','2015-05-12','2015-05-13','2015-05-14','2015-05-15','2015-05-18','2015-05-19','2015-05-20','2015-05-21','2015-05-22','2015-05-26','2015-05-27','2015-05-28','2015-05-29','2015-06-01','2015-06-02','2015-06-03','2015-06-04','2015-06-05','2015-06-08','2015-06-09','2015-06-10','2015-06-11','2015-06-12','2015-06-15','2015-06-16','2015-06-17','2015-06-18','2015-06-19','2015-06-22','2015-06-23','2015-06-24','2015-06-25','2015-06-26','2015-06-29','2015-06-30','2015-07-01','2015-07-02','2015-07-06','2015-07-07','2015-07-08','2015-07-09','2015-07-10','2015-07-13','2015-07-14','2015-07-15','2015-07-16','2015-07-17','2015-07-20','2015-07-21','2015-07-22','2015-07-23','2015-07-24','2015-07-27','2015-07-28','2015-07-29','2015-07-30','2015-07-31','2015-08-03','2015-08-04','2015-08-05','2015-08-06','2015-08-07','2015-08-10','2015-08-11','2015-08-12','2015-08-13','2015-08-14','2015-08-17','2015-08-18','2015-08-19','2015-08-20','2015-08-21','2015-08-24','2015-08-25','2015-08-26','2015-08-27','2015-08-28','2015-09-01','2015-09-02','2015-09-03','2015-09-04','2015-09-08','2015-09-09','2015-09-10','2015-09-11','2015-09-14']
#
#for i in range(len(dateVec)):
#    ycVec[i] = yieldCurve(dateVec[i])

#ycVec = []
#dateVec = ['2012-01-03','2012-02-01','2012-03-01','2012-03-29','2012-04-26','2012-05-24','2012-06-22','2012-07-23','2012-08-20','2012-09-18','2012-10-17','2012-11-15','2012-12-14','2013-01-15','2013-02-13','2013-03-14','2013-04-11','2013-05-09','2013-06-07','2013-07-08','2013-08-05','2013-09-03','2013-10-01','2013-10-30','2013-11-29','2013-12-30','2014-01-29','2014-02-27','2014-03-27','2014-04-24','2014-05-22','2014-06-20','2014-07-21','2014-08-18','2014-09-16','2014-10-15','2014-11-13','2014-12-12','2015-01-13','2015-02-11','2015-03-12','2015-04-09','2015-05-07','2015-06-05','2015-07-06','2015-08-03','2015-08-28','2015-09-29','2015-10-28','2015-11-27','2015-12-29','2016-01-22']
#for i in range(len(dateVec)):
#    ycVec.append(yieldCurve(dateVec[i]))
