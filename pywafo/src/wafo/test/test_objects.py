# -*- coding:utf-8 -*-
"""
Created on 5. aug. 2010

@author: pab
"""
import wafo.data
import numpy as np

def test_timeseries():
    '''
    >>> import wafo.data
    >>> import wafo.objects as wo
    >>> x = wafo.data.sea()
    >>> ts = wo.mat2timeseries(x)
    >>> ts.sampling_period()
    0.25
    
    Estimate spectrum
    >>> S = ts.tospecdata()
    The default L is set to 325
    >>> S.data[:10]
    array([ 0.00913087,  0.00881073,  0.00791944,  0.00664244,  0.00522429,
            0.00389816,  0.00282753,  0.00207843,  0.00162678,  0.0013916 ])
            
    Estimated covariance function
    >>> rf = ts.tocovdata(lag=150)
    >>> rf.data[:10]
    array([ 0.22368637,  0.20838473,  0.17110733,  0.12237803,  0.07024054,
            0.02064859, -0.02218831, -0.0555993 , -0.07859847, -0.09166187])
    '''
def test_timeseries_trdata():
    '''
    >>> import wafo.spectrum.models as sm
    >>> import wafo.transform.models as tm
    >>> from wafo.objects import mat2timeseries
    >>> Hs = 7.0
    >>> Sj = sm.Jonswap(Hm0=Hs)
    >>> S = Sj.tospecdata()   #Make spectrum object from numerical values
    >>> S.tr = tm.TrOchi(mean=0, skew=0.16, kurt=0, sigma=Hs/4, ysigma=Hs/4)
    >>> xs = S.sim(ns=2**20)
    >>> ts = mat2timeseries(xs)
    >>> g0, gemp = ts.trdata(monitor=True) # Monitor the development
    >>> g1, gemp = ts.trdata(method='m', gvar=0.5 ) # Equal weight on all points
    >>> g2, gemp = ts.trdata(method='n', gvar=[3.5, 0.5, 3.5])  # Less weight on the ends
    >>> S.tr.dist2gauss()
    1.4106988010566603
    >>> np.round(g0.dist2gauss())
    1.0
    >>> np.round(g1.dist2gauss())
    1.0
    >>> np.round(g2.dist2gauss())
    1.0
  
    '''
if __name__=='__main__':
    import doctest
    doctest.testmod()