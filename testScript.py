# -*- coding: utf-8 -*-
"""
Created on Sat Jan 30 13:40:48 2016

@author: jaycw_000
"""

import pandas as pd
import numpy as np

def plotCurve(curve):
    plot(curve.swapData)

s2  = np.zeros(len(ycVec))
s10 = np.zeros(len(ycVec))
s30 = np.zeros(len(ycVec))

fs2  = np.zeros(len(ycVec))
fs10 = np.zeros(len(ycVec))
fs30 = np.zeros(len(ycVec))

#spot fly
for i in range(len(ycVec)):
    s2[i]  = ycVec[i].swapRate(0,2)
    s10[i] = ycVec[i].swapRate(0,10)
    s30[i] = ycVec[i].swapRate(0,30)
    fs2[i]  = ycVec[i].swapRate(1,2)
    fs10[i] = ycVec[i].swapRate(1,10)
    fs30[i] = ycVec[i].swapRate(1,30)

spotFly = -s2 + 2 * s10 - s30
pcaFly  = -s2 +     s10 - s30

fspotFly = -fs2 + 2 * fs10 - fs30
fpcaFly  = -fs2 +     fs10 - fs30

