"""
    Modify this file if another plotbackend is wanted.
"""
import warnings
verbose = False
if False:
    try:
        from scitools import easyviz as plotbackend
        if verbose:
            print('wafo.wafodata: plotbackend is set to scitools.easyviz')
    except:
        warnings.warn('wafo: Unable to load scitools.easyviz as plotbackend')
        plotbackend = None
else:
    try:
        from matplotlib import pyplot as plotbackend
        plotbackend.interactive(True)
        if verbose:
            print('wafo.wafodata: plotbackend is set to matplotlib.pyplot')
    except:
        warnings.warn('wafo: Unable to load matplotlib.pyplot as plotbackend')
        plotbackend = None