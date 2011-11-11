"""
Impulse reponse-related code
"""

from __future__ import division

import numpy as np
import numpy.linalg as la
import scipy.linalg as L

from scipy import stats

from scikits.statsmodels.tools.decorators import cache_readonly
from scikits.statsmodels.tools.tools import chain_dot
#from scikits.statsmodels.tsa.api import VAR

import scikits.statsmodels.tsa.tsatools as tsa
import scikits.statsmodels.tsa.vector_ar.plotting as plotting
import scikits.statsmodels.tsa.vector_ar.util as util

mat = np.array

class BaseIRAnalysis(object):
    """
    Base class for plotting and computing IRF-related statistics, want to be
    able to handle known and estimated processes
    """

    def __init__(self, model, P=None, periods=10, order=None):
        self.model = model
        self.periods = periods
        self.neqs, self.lags, self.T  = model.neqs, model.k_ar, model.nobs

        self.order = order

        if P is None:
            sigma = model.sigma_u

            # TODO, may be difficult at the moment
            # if order is not None:
            #     indexer = [model.get_eq_index(name) for name in order]
            #     sigma = sigma[:, indexer][indexer, :]

            #     if sigma.shape != model.sigma_u.shape:
            #         raise ValueError('variable order is wrong length')

            P = la.cholesky(sigma)

        self.P = P

        self.irfs = model.ma_rep(periods)
        self.orth_irfs = model.orth_ma_rep(periods)

        self.cum_effects = self.irfs.cumsum(axis=0)
        self.orth_cum_effects = self.orth_irfs.cumsum(axis=0)

        self.lr_effects = model.long_run_effects()
        self.orth_lr_effects = np.dot(model.long_run_effects(), P)

        # auxiliary stuff
        self._A = util.comp_matrix(model.coefs)

    def cov(self, *args, **kwargs):
        raise NotImplementedError

    def cum_effect_cov(self, *args, **kwargs):
        raise NotImplementedError

    def plot(self, orth=False, impulse=None, response=None, signif=0.05,
             plot_params=None, subplot_params=None, plot_stderr=True,
             stderr_type='asym', repl=1000, seed=None):
        """
        Plot impulse responses

        Parameters
        ----------
        orth : bool, default False
            Compute orthogonalized impulse responses
        impulse : string or int
            variable providing the impulse
        response : string or int
            variable affected by the impulse
        signif : float (0 < signif < 1)
            Significance level for error bars, defaults to 95% CI
        subplot_params : dict
            To pass to subplot plotting funcions. Example: if fonts are too big,
            pass {'fontsize' : 8} or some number to your taste.
        plot_params : dict

        plot_stderr: bool, default True
            Plot standard impulse response error bands
        stderr_type: string
            'asym': default, computes asymptotic standard errors
            'mc': monte carlo standard errors (use rpl)
        repl: int, default 1000
            Number of replications for monte carlo standard errors
        seed: int
            np.random.seed for Monte Carlo replications
        """
        periods = self.periods
        model = self.model

        if orth:
            title = 'Impulse responses (orthogonalized)'
            irfs = self.orth_irfs
        else:
            title = 'Impulse responses'
            irfs = self.irfs

        if stderr_type not in ['asym','mc']:
            raise TypeError
        else:
            if stderr_type == 'asym':
                stderr = self.cov(orth=orth)
            if stderr_type == 'mc':
                stderr = self.cov_mc(orth=orth, repl=repl,
                                     signif=signif, seed=seed)
        plotting.irf_grid_plot(irfs, stderr, impulse, response,
                               self.model.names, title, signif=signif,
                               subplot_params=subplot_params,
                               plot_params=plot_params, stderr_type=stderr_type)

    def plot_cum_effects(self, orth=False, impulse=None, response=None,
                         signif=0.05, plot_params=None,
                         subplot_params=None, plot_stderr=True):
        """

        """

        if orth:
            title = 'Cumulative responses responses (orthogonalized)'
            cum_effects = self.orth_cum_effects
            lr_effects = self.orth_lr_effects
        else:
            title = 'Cumulative responses'
            cum_effects = self.cum_effects
            lr_effects = self.lr_effects

        try:
            stderr = self.cum_effect_cov(orth=orth)
        except NotImplementedError: # pragma: no cover
            stderr = None

        if not plot_stderr:
            stderr = None

        plotting.irf_grid_plot(cum_effects, stderr, impulse, response,
                               self.model.names, title, signif=signif,
                               hlines=lr_effects, subplot_params=subplot_params,
                               plot_params=plot_params, stderr_type='asym')

class IRAnalysis(BaseIRAnalysis):
    """
    Impulse response analysis class. Computes impulse responses, asymptotic
    standard errors, and produces relevant plots

    Parameters
    ----------
    model : VAR instance

    Notes
    -----
    Using Lutkepohl (2005) notation
    """
    def __init__(self, model, P=None, periods=10, order=None):
        BaseIRAnalysis.__init__(self, model, P=P, periods=periods,
                                order=order)

        self.cov_a = model._cov_alpha
        self.cov_sig = model._cov_sigma

        # memoize dict for G matrix function
        self._g_memo = {}

    def cov(self, orth=False):
        """
        Compute asymptotic standard errors for impulse response coefficients

        Notes
        -----
        Lutkepohl eq 3.7.5

        Returns
        -------
        """
        if orth:
            return self._orth_cov()

        covs = self._empty_covm(self.periods + 1)
        covs[0] = np.zeros((self.neqs ** 2, self.neqs ** 2))
        for i in range(1, self.periods + 1):
            Gi = self.G[i - 1]
            covs[i] = chain_dot(Gi, self.cov_a, Gi.T)

        return covs

    def cov_mc(self, orth=False, repl=1000, signif=0.05, seed=None):
        """
        IRF Monte Carlo standard errors
        """
        model = self.model
        periods = self.periods
        return model.stderr_MC_irf(orth=orth, repl=repl,
                                    T=periods, signif=signif, seed=seed)

    @cache_readonly
    def G(self):
        # Gi matrices as defined on p. 111

        K = self.neqs

        # nlags = self.model.p
        # J = np.hstack((np.eye(K),) + (np.zeros((K, K)),) * (nlags - 1))

        def _make_g(i):
            # p. 111 Lutkepohl
            G = 0.
            for m in range(i):
                # be a bit cute to go faster
                idx = i - 1 - m
                if idx in self._g_memo:
                    apow = self._g_memo[idx]
                else:
                    apow = la.matrix_power(self._A.T, idx)
                    # apow = np.dot(J, apow)
                    apow = apow[:K]
                    self._g_memo[idx] = apow

                # take first K rows
                piece = np.kron(apow, self.irfs[m])
                G = G + piece

            return G

        return [_make_g(i) for i in range(1, self.periods + 1)]

    def _orth_cov(self):
        # Lutkepohl 3.7.8

        Ik = np.eye(self.neqs)
        PIk = np.kron(self.P.T, Ik)
        H = self.H

        covs = self._empty_covm(self.periods + 1)
        for i in range(self.periods + 1):
            if i == 0:
                apiece = 0
            else:
                Ci = np.dot(PIk, self.G[i-1])
                apiece = chain_dot(Ci, self.cov_a, Ci.T)

            Cibar = np.dot(np.kron(Ik, self.irfs[i]), H)
            bpiece = chain_dot(Cibar, self.cov_sig, Cibar.T) / self.T

            # Lutkepohl typo, cov_sig correct
            covs[i] = apiece + bpiece

        return covs

    def cum_effect_cov(self, orth=False):
        """
        Compute asymptotic standard errors for cumulative impulse response
        coefficients

        Parameters
        ----------
        orth : boolean

        Notes
        -----
        eq. 3.7.7 (non-orth), 3.7.10 (orth)

        Returns
        -------

        """
        Ik = np.eye(self.neqs)
        PIk = np.kron(self.P.T, Ik)

        F = 0.
        covs = self._empty_covm(self.periods + 1)
        for i in range(self.periods + 1):
            if i > 0:
                F = F + self.G[i - 1]

            if orth:
                if i == 0:
                    apiece = 0
                else:
                    Bn = np.dot(PIk, F)
                    apiece = chain_dot(Bn, self.cov_a, Bn.T)

                Bnbar = np.dot(np.kron(Ik, self.cum_effects[i]), self.H)
                bpiece = chain_dot(Bnbar, self.cov_sig, Bnbar.T) / self.T

                covs[i] = apiece + bpiece
            else:
                if i == 0:
                    covs[i] = np.zeros((self.neqs**2, self.neqs**2))
                    continue

                covs[i] = chain_dot(F, self.cov_a, F.T)

        return covs

    def lr_effect_cov(self, orth=False):
        """

        Returns
        -------

        """
        lre = self.lr_effects
        Finfty = np.kron(np.tile(lre.T, self.lags), lre)
        Ik = np.eye(self.neqs)

        if orth:
            Binf = np.dot(np.kron(self.P.T, np.eye(self.neqs)), Finfty)
            Binfbar = np.dot(np.kron(Ik, lre), self.H)

            return (chain_dot(Binf, self.cov_a, Binf.T) +
                    chain_dot(Binfbar, self.cov_sig, Binfbar.T))
        else:
            return chain_dot(Finfty, self.cov_a, Finfty.T)

    def stderr(self, orth=False):
        return np.array([tsa.unvec(np.sqrt(np.diag(c)))
                         for c in self.cov(orth=orth)])

    def cum_effect_stderr(self, orth=False):
        return np.array([tsa.unvec(np.sqrt(np.diag(c)))
                         for c in self.cum_effect_cov(orth=orth)])

    def lr_effect_stderr(self, orth=False):
        cov = self.lr_effect_cov(orth=orth)
        return tsa.unvec(np.sqrt(np.diag(cov)))

    def _empty_covm(self, periods):
        return np.zeros((periods, self.neqs ** 2, self.neqs ** 2),
                        dtype=float)

    @cache_readonly
    def H(self):
        k = self.neqs
        Lk = tsa.elimination_matrix(k)
        Kkk = tsa.commutation_matrix(k, k)
        Ik = np.eye(k)

        # B = chain_dot(Lk, np.eye(k**2) + commutation_matrix(k, k),
        #               np.kron(self.P, np.eye(k)), Lk.T)

        # return np.dot(Lk.T, L.inv(B))

        B = chain_dot(Lk,
                      np.dot(np.kron(Ik, self.P), Kkk) + np.kron(self.P, Ik),
                      Lk.T)

        return np.dot(Lk.T, L.inv(B))

    def fevd_table(self):
        pass
