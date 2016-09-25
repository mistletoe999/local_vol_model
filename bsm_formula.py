#
# Valuation of European call options in Black-Scholes-Merton model
# incl. Vega function and implied volatility estimation
# bsm_functions.py
#

# Analytical Black-Scholes-Merton (BSM) Formula

from math import log, sqrt, exp, fabs
from scipy import stats

def bsm_call_value(S0, K, T, r, q, sigma):
    ''' Valuation of European call option in BSM model.
    Analytical formula.
    Parameters
    ==========
    S0 : float
        initial stock/index level
    K : float
        strike price
    T : float
        maturity date (in year fractions)
    r : float
        constant risk-free short rate
    q : float
        constant dividend rate
    sigma : float
        volatility factor in diffusion term
    Returns
    =======
    value : float
        present value of the European call option
    '''

    S0 = float(S0)
    d1 = (log(S0 / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))
    d2 = (log(S0 / K) + (r - q - 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))
    value = S0 * exp(-q * T) * stats.norm.cdf(d1, 0.0, 1.0) \
        - K * exp(-r * T) * stats.norm.cdf(d2, 0.0, 1.0)
        # stats.norm.cdf --> cumulative distribution function
        #                    for normal distribution
    return value


# Vega function
def bsm_vega(S0, K, T, r, q, sigma):
    ''' Vega of European option in BSM model.
    Parameters
    ==========
    S0 : float
        initial stock/index level
    K : float
        strike price
    T : float
        maturity date (in year fractions)
    r : float
        constant risk-free short rate
    q : float
        constant dividend rate
    sigma : float
        volatility factor in diffusion term
    Returns
    =======
    vega : float
    partial derivative of BSM formula with respect
    to sigma, i.e. Vega
    '''

    S0 = float(S0)
    d1 = (log(S0 / K) + (r - q + 0.5 * sigma ** 2) * T ) / (sigma * sqrt(T))
    vega = S0 * exp(-q * T) * stats.norm.pdf(d1, 0.0, 1.0) * sqrt(T)
    return vega


# Implied volatility function
def bsm_call_imp_vol(S0, K, T, r, q, C0, sigma_est, epsilon = 0.000001):
    ''' Implied volatility of European call option in BSM model.
    Parameters
    ==========
    S0 : float
        initial stock/index level
    K : float
        strike price
    T : float
        maturity date (in year fractions)
    r : float
        constant risk-free short rate
    q : float
        constant dividend rate
    sigma_est : float
        estimate of impl. volatility
    epsilon : float
        estimation error
    Returns
    =======
    simga_est : float
        numerically estimated implied volatility
    '''

    sigma_est_pre = 0
    while (fabs(sigma_est - sigma_est_pre) > epsilon):
        sigma_est_pre = sigma_est
        sigma_est -= (bsm_call_value(S0, K, T, r, q, sigma_est) - C0) \
            / bsm_vega(S0, K, T, r, q, sigma_est)
        #print bsm_vega(S0, K, T, r, q, sigma_est)
    
    return sigma_est