# -*- coding: utf-8 -*-
"""
Created on Thu Dec 17 17:24:47 2015

@author: jaycw_000
"""

testCurve = ycVec[0]
ycTestVec = [None] * 11

for i in range(11):
    ycTestVec[i] = yieldCurve(testCurve.returnDate(),testCurve.bump(10*i))
    print ycTestVec[i].discFact(3.4)