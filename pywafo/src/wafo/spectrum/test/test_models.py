import numpy as np
from wafo.spectrum.models import (Bretschneider, Jonswap, OchiHubble, Tmaspec, 
                                  Torsethaugen, McCormick, Wallop)

def test_bretschneider():
    S = Bretschneider(Hm0=6.5,Tp=10)
    vals =  S((0,1,2,3))
    true_vals = np.array([ 0.        ,  1.69350993,  0.06352698,  0.00844783])
    assert((np.abs(vals-true_vals)<1e-7).all())
    
def test_if_jonswap_with_gamma_one_equals_bretschneider():
    S = Jonswap(Hm0=7, Tp=11,gamma=1)
    vals = S((0,1,2,3))
    true_vals = np.array([ 0.        ,  1.42694133,  0.05051648,  0.00669692])
    assert((np.abs(vals-true_vals)<1e-7).all())
    
    w = np.linspace(0,5)
    S2 = Bretschneider(Hm0=7, Tp=11)
    #JONSWAP with gamma=1 should be equal to Bretscneider:
    assert(np.all(np.abs(S(w)-S2(w))<1.e-7))
    

def test_tmaspec():
    S = Tmaspec(Hm0=7, Tp=11,gamma=1,h=10)
    vals = S((0,1,2,3))
    true_vals = np.array([ 0.        ,  0.70106233,  0.05022433,  0.00669692])
    assert((np.abs(vals-true_vals)<1e-7).all())
    
def test_torsethaugen():
    
    S = Torsethaugen(Hm0=7, Tp=11,gamma=1,h=10)
    vals = S((0,1,2,3))
    true_vals = np.array([ 0.        ,  1.19989709,  0.05819794,  0.0093541 ])
    assert((np.abs(vals-true_vals)<1e-7).all())
    
    vals = S.wind(range(4))
    true_vals = np.array([ 0.        ,  1.13560528,  0.05529849,  0.00888989])
    assert((np.abs(vals-true_vals)<1e-7).all())
    vals = S.swell(range(4))
    true_vals = np.array([ 0.        ,  0.0642918 ,  0.00289946,  0.00046421])
    assert((np.abs(vals-true_vals)<1e-7).all())

def test_ochihubble():
    
    S = OchiHubble(par=2)
    vals = S(range(4))
    true_vals = np.array([ 0.        ,  0.90155636,  0.04185445,  0.00583207])
    assert((np.abs(vals-true_vals)<1e-7).all())
    
def test_mccormick():
    
    S = McCormick(Hm0=6.5,Tp=10)
    vals = S(range(4))
    true_vals = np.array([ 0.        ,  1.87865908,  0.15050447,  0.02994663])
    assert((np.abs(vals-true_vals)<1e-7).all())
    
def test_wallop():
    
    S = Wallop(Hm0=6.5, Tp=10)
    vals = S(range(4))
    true_vals = np.array([  0.00000000e+00,   9.36921871e-01,   2.76991078e-03,
             7.72996150e-05])
    assert((np.abs(vals-true_vals)<1e-7).all())
    

if __name__ == '__main__':
    #main()
    import nose
#    nose.run()
    test_tmaspec()