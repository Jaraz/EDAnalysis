from __future__ import division
from matplotlib import pyplot
import pandas
import numpy
#import EDFutures.py
#import swapCurve.py


########################################################
##### Show pnl path of a past convexity bias trade #####
########################################################

#assumes 100mm fra and 96 static hedge portfoio (takes a curve vector isntead) 
def realizedCvxBiasV2(dateVec, edObj, curveVec, contract, dynamicHedge=False):
    startRate = edObj.edRates[edObj.edDict[contract]][dateVec[0]]
    pnlVec = numpy.zeros(len(dateVec))
    rateVec = numpy.zeros(len(dateVec))
    ycDate = (numpy.datetime64(edObj.dates[contract])-numpy.datetime64(dateVec[0]))/numpy.timedelta64(1,'D')/365
    futureHedgeRatio = round(curveVec[0].discFact(ycDate+0.25)*100,0)

    hedgeTrack = pandas.DataFrame(index=[dateVec],columns=["strike","contracts"])
    
    for i in range(1,len(dateVec)):
        newRate = edObj.edRates[edObj.edDict[contract]][dateVec[i]]
        yc = curveVec[i]  #use YC for discounting
        ycDate = (numpy.datetime64(edObj.dates[contract])-numpy.datetime64(dateVec[i]))/numpy.timedelta64(1,'D')/365
        df = yc.discFact(ycDate+0.25)
        
        fraPnL = (newRate - startRate)/100 * df / 4 * 100000000
        futPnL = -(newRate - startRate) * 100 * 25* futureHedgeRatio
        pnlVec[i] = fraPnL + futPnL
        rateVec[i] = (newRate - startRate)
        
        #rehedge at end of day
        if dynamicHedge:
            temp = round(df*100,0)
            hedgeTrack["contracts"][i] = temp - futureHedgeRatio
            hedgeTrack["strike"][i] = edObj.edRates[edObj.edDict[contract]][dateVec[i]]
            
            futureHedgeRatio = temp

    return rateVec, pnlVec, hedgeTrack

#assumes 100mm fra and 96 static hedge portfoio (not perfect but quick enough) 
def realizedCvxBias(dateVec, edObj, contract):
    startRate = edObj.edRates[edObj.edDict[contract]][dateVec[0]]
    pnlVec = numpy.zeros(len(dateVec))
    rateVec = numpy.zeros(len(dateVec))
    futureHedgeRatio = 96
    currentRate = startRate
    for i in range(1,len(dateVec)):
        newRate = edObj.edRates[edObj.edDict[contract]][dateVec[i]]
        yc = yieldCurve(dateVec[i])  #use YC for discounting
        ycDate = (numpy.datetime64(edObj.dates[contract])-numpy.datetime64(dateVec[i]))/numpy.timedelta64(1,'D')/365
        df = yc.discFact(ycDate+0.25)
        fraPnL = (newRate - startRate)/100 * df / 4 * 100000000
        futPnL = -(newRate - startRate) * 100 * 25* futureHedgeRatio
        pnlVec[i] = fraPnL + futPnL
        rateVec[i] = (newRate - startRate)

    return rateVec, pnlVec

##################################################
##### Show convexity of FRA vs Futures Trade #####
##################################################

#This function assumes we are rec fixed and have hedge ourselves with a pay fixed future contract, size based on discounting from tehe libor curve - believe this should be ideally OIS now 
#Assume both fra and futures move at the same rate - takes a YC input, then bumps to rebuild to see change in fwds + discount factor
def FRAvFut(start, curveObj):  #paying fixed on 100mm contract - returns a dataframe
    fraRate  = curveObj.fwdRate(start) * 10000
    
    #due to discounting we won't need 1:1 futures to cover our 100mm FRA
    futureHedgeRatio = curveObj.discFact(start+0.25)

    #FRA Payoffs
    shifts = numpy.linspace(-20,20,5)
    fraResult = numpy.zeros(5)
    futResult = numpy.zeros(5)
    fraRates   = numpy.zeros(5)
    discFacts = numpy.zeros(5)
        
    ycDown20 = yieldCurve(curveObj.returnDate, curveObj.bump(shifts[0]))    
    ycDown10 = yieldCurve(curveObj.returnDate, curveObj.bump(shifts[1]))

    ycUp10 = yieldCurve(curveObj.returnDate, curveObj.bump(shifts[3]))
    ycUp20 = yieldCurve(curveObj.returnDate, curveObj.bump(shifts[4]))
    
    fraResult[4] = fraPayoff(start,fraRate,ycDown20) * 1e8
    fraResult[3] = fraPayoff(start,fraRate,ycDown10) * 1e8
    fraResult[2] = fraPayoff(start,fraRate,curveObj) * 1e8
    fraResult[1] = fraPayoff(start,fraRate,ycUp10) * 1e8
    fraResult[0] = fraPayoff(start,fraRate,ycUp20) * 1e8

    #Future Payoffs
    futResult[4] = (ycDown20.fwdRate(start)-curveObj.fwdRate(start)) * 25 * 1000000 * futureHedgeRatio
    futResult[3] = (ycDown10.fwdRate(start)-curveObj.fwdRate(start)) * 25 * 1000000 * futureHedgeRatio
    futResult[2] = 0
    futResult[1] = (ycUp10.fwdRate(start)-curveObj.fwdRate(start)) * 25 * 1000000 * futureHedgeRatio
    futResult[0] = (ycUp20.fwdRate(start)-curveObj.fwdRate(start)) * 25 * 1000000 * futureHedgeRatio
    
    fraRates[4]   = ycDown20.fwdRate(start)
    fraRates[3]   = ycDown10.fwdRate(start)
    fraRates[2]   = curveObj.fwdRate(start)
    fraRates[1]   = ycUp10.fwdRate(start)
    fraRates[0]   = ycUp20.fwdRate(start)
    
    discFacts[4] = ycDown20.discFact(start+0.25)
    discFacts[3] = ycDown10.discFact(start+0.25)
    discFacts[2] = curveObj.discFact(start+0.25)
    discFacts[1] = ycUp10.discFact(start+0.25)
    discFacts[0] = ycUp20.discFact(start+0.25)
    
    answer = pandas.DataFrame(data  =['+20bps','+10bps','0bps','-10bps','-20bps'])
    answer['FRA Rate'] = fraRates * 10000
    answer['Disc Fact'] = discFacts
    answer['FRA PnL'] = fraResult
    answer['Fut PnL'] = futResult
    answer['Net Pnl'] = futResult + fraResult

    return answer


def plotED(edObj, contract, realizedDays=30):
    table = edObj.runAnalysis(contract, realizedDays)
    fig, ax1 = pyplot.subplots()
    ax1.plot(table.index, table["Rates"] * 100, color='b')    
    ax1.set_ylabel("Rate (bps)", color = 'b')
    
    ax2 = ax1.twinx()    
    ax2.plot(table.index, table["Realized Vol"],color='g')   
    ax2.set_ylabel("Realized Vol (bps/ann)", color = 'g')
    
    pyplot.show()

#give date vector + ed obj and it will build yc and compare implied fwds // Contract should be first of whites
def cvxAnalysis(edObj, dateVec, contract):
    answer = pandas.DataFrame(index = dateVec, columns=['reds','greens','blues'])    
    for i in range(len(dateVec)):
        yc = yieldCurve(dateVec[i])
        temp = convexityCompare(edObj,yc,dateVec[i],contract)
        answer['reds'][dateVec[i]] = temp['Diff']['reds']
        answer['greens'][dateVec[i]]   = temp['Diff']['greens']
        answer['blues'][dateVec[i]] = temp['Diff']['blues']
    return answer

#contract input is the first reds contract
def convexityCompare(edObj, ycObj, date, contract):
    ycDate = (numpy.datetime64(edObj.dates[contract])-numpy.datetime64(date))/numpy.timedelta64(1,'D')/365
    edRates = edObj.returnColors(contract,date)
    print ycDate
    swapsWhites = swapRate(ycDate,1,ycObj)
    swapsReds = swapRate(ycDate+1,1,ycObj)
    swapsGreens = swapRate(ycDate+2,1,ycObj)
    edRates.loc['Swaps'] = [swapsWhites,swapsReds,swapsGreens]
    edRates = edRates.T
    edRates['Diff']  = edRates['Futures'] - edRates['Swaps']
    
    return edRatesa

cvxBiasDates = ['2015-08-03','2015-08-04','2015-08-05','2015-08-06','2015-08-07','2015-08-10','2015-08-11','2015-08-12','2015-08-13','2015-08-14','2015-08-17','2015-08-18','2015-08-19','2015-08-20','2015-08-21','2015-08-24','2015-08-25','2015-08-26','2015-08-27','2015-08-28','2015-09-02','2015-09-03','2015-09-04','2015-09-08','2015-09-09','2015-09-10','2015-09-11','2015-09-14','2015-09-15','2015-09-16','2015-09-17','2015-09-18','2015-09-21','2015-09-22','2015-09-23','2015-09-24','2015-09-25','2015-09-28','2015-09-29','2015-09-30','2015-10-01','2015-10-02','2015-10-05','2015-10-06','2015-10-07','2015-10-08','2015-10-09','2015-10-13','2015-10-14','2015-10-15','2015-10-16','2015-10-19','2015-10-20','2015-10-21','2015-10-22','2015-10-23','2015-10-26','2015-10-27','2015-10-28','2015-10-29','2015-10-30']
#cvxBiasDates = ['2015-08-03','2015-08-04','2015-08-05','2015-08-06','2015-08-07','2015-08-10','2015-08-11','2015-08-12','2015-08-13','2015-08-14','2015-08-17','2015-08-18']

rateResults, pnlResults, costOfHedge= realizedCvxBiasV2(dateVec,ed,ycVec,20,True)

results = pandas.DataFrame(rateResults, columns=["Rate Change"])
results["PnL"] = pnlResults
pyplot.scatter(results["Rate Change"]*100,results["PnL"])


#Nov 2015 - Function is comparing bootstrapped fwd swap rates vs futures // average and scrub data in excel as swaps are 11am, which causes a problem
#nov15List = ['2015-11-02','2015-11-03','2015-11-04','2015-11-05','2015-11-06','2015-11-09','2015-11-10','2015-11-12','2015-11-13','2015-11-16','2015-11-17','2015-11-18','2015-11-19','2015-11-20','2015-11-23','2015-11-24','2015-11-25','2015-11-27','2015-11-30']
#convexityAvgNov15 = cvxAnalysis(ed,nov15List,12)

#test1 pack starting at Dec15
#realized = 30
#test1, test2, test3 = ed.runRealizedColors(8,realized)
#print "2013 Reds:",test1["Realized Vol"]['2013-11-29'], test2["Realized Vol"]['2013-11-29'],test3["Realized Vol"]['2013-11-29']
#print "2013 Reds:",numpy.sqrt(numpy.mean(numpy.power(test1['2013-09-22':'2013-12-15']["Realized Vol"],2)))
#print "2013 Greens:",numpy.sqrt(numpy.mean(numpy.power(test2['2013-09-22':'2013-12-15']["Realized Vol"],2)))
#print "2013 Blues:",numpy.sqrt(numpy.mean(numpy.power(test3['2013-09-22':'2013-12-15']["Realized Vol"],2)))

#test1, test2, test3 = ed.runRealizedColors(12,realized)
#print "2014 Reds:",test1["Realized Vol"]['2014-11-28'], test2["Realized Vol"]['2014-11-28'],test3["Realized Vol"]['2014-11-28']
#print "2014 Reds:",numpy.sqrt(numpy.mean(numpy.power(test1['2014-09-22':'2014-12-15']["Realized Vol"],2)))
#print "2014 Greens:",numpy.sqrt(numpy.mean(numpy.power(test2['2014-09-22':'2014-12-15']["Realized Vol"],2)))
#print "2014 Blues:",numpy.sqrt(numpy.mean(numpy.power(test3['2014-09-22':'2014-12-15']["Realized Vol"],2)))

#test1, test2, test3 = ed.runRealizedColors(16,realized)
#print "2015 Reds:",test1["Realized Vol"]['2015-11-30'], test2["Realized Vol"]['2015-11-30'],test3["Realized Vol"]['2015-11-30']
#print "2015 Reds:",numpy.sqrt(numpy.mean(numpy.power(test1['2015-09-22':'2015-12-08']["Realized Vol"],2)))
#print "2015 Greens:",numpy.sqrt(numpy.mean(numpy.power(test2['2015-09-22':'2015-12-08']["Realized Vol"],2)))
#print "2015 Blues:",numpy.sqrt(numpy.mean(numpy.power(test3['2015-09-22':'2015-12-08']["Realized Vol"],2)))