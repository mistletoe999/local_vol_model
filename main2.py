# main.py

import datetime as dt
import numpy as np
import pandas as pd

import calibrate
import curves
import data
import volatility

if __name__ == '__main__':


    # Import the evaluation date and spot price
    file_path = '../data_graphs/MarketData20160614.xlsx'
    market_data = pd.read_excel(file_path, 'Menu')
    evaluation_date = dt.datetime.date(market_data['Value'][0])
    spot = market_data['Value'][1]
    vix = market_data['Value'][2]

    # Import and plot time series of SPX and VIX
    #start_date = dt.datetime.date(dt.datetime(2000, 1, 1))
    #end_date = evaluation_date
    #market_data = data.DataHandler()
    #market_data.printData()
    #market_data.SPXVIXPlot(start_date, end_date)

    # Build the yield curve from money market instruments 
    # (rates, futures and swaps of LIBOR)
    #yieldCurve = curves.YieldCurve(marketData.liborChain)
    #yieldCurve.discountCurve()
    #yieldCurve.instForwardRateCurve()

    # Build the yield curve and dividend curve
    rates_data = pd.read_excel(file_path, 'SPXImpliedDvdAdj', index_col = 0)
    maturity_dates = rates_data.index
    zero_rates = rates_data['Risk Free'].values
    dividend_rates = rates_data['Impl (Yld)'].values
    yield_curve = curves.ZeroRateCurve(evaluation_date, 
        maturity_dates, zero_rates)
    dividend_curve = curves.ZeroRateCurve(evaluation_date, 
        maturity_dates, dividend_rates)
    
    # Plot the instantaneous forward rates 
    #time_to_maturities = np.linspace(0.01, 1, 100)
    #yield_curve.inst_forward_rate_plot(time_to_maturities, 
    #    'time-to-maturity', 'instantaneous forward rate', 
    #    '../Data/YieldForwardCurve.png')
    #dividend_curve.inst_forward_rate_plot(time_to_maturities, 
    #    'time-to-maturity', 'instantaneous forward rate', 
    #    '../Data/DividendForwardCurve.png')


    # Build the variance swap term structure
    #var_swap_data = pd.read_excel(file_path, 'VarSwapsAdj', index_col = 0)
    # maturity_dates = var_swap_data.index
    # var_swap_rates = (var_swap_data['Continuous Mid/Settle'].values 
        # / 100.0) ** 2
    # var_swap_curve = curves.ZeroRateCurve(evaluation_date, 
        # maturity_dates, var_swap_rates)

    # Plot the variance swap term structure
    # time_to_maturities = np.linspace(0.05, 2, 100)
    #var_swap_curve.zero_curve_plot(time_to_maturities, 'time-to-maturity', 
    #    'variance swap rate', '../Data/VarSwapRate.png')

    # Build the implied/local volatility suraface 
    implied_vol_data = pd.read_excel(file_path, 'SPXImpliedVolAdj', 
        index_col = 0)          # (maturity_date, strike)
    maturity_dates = implied_vol_data.index
    strikes = implied_vol_data.columns.values
    implied_vol_matrix = np.transpose(implied_vol_data.as_matrix()) / 100.0
         # (strike, maturity_date)
    volatility_surface = volatility.VolatilitySurface(
        evaluation_date, maturity_dates, 
        strikes, implied_vol_matrix, spot,
        yield_curve, dividend_curve)

    # Plot the implied/local volatility suraface 
    strikes = np.linspace(1700.0, 2400.0, 17)
    time_to_maturities = np.linspace(0.0, 2.0, 17)
    time_to_maturities[0] = 0.01
    volatility_surface.surface_plot(strikes, time_to_maturities, 
        '../data_graphs/VolSurface.png')

    # Build the dynamic local volatility suraface 
    dynamic_local_vol = volatility.DynamicLocalVolSurface(
        volatility_surface, spot, yield_curve, dividend_curve, 
        months = 8, grids_per_month = 1, deltax_per_month = 0.20)

    # Import the VIX option data
    vix_option_data = pd.read_excel(file_path, 'VIXOptionsAdj')    
    vix_option_data['TTM'] = [ item.days / 365.0
        for item in vix_option_data['Maturity'] - evaluation_date ] 
    vix_option_data['ZeroRate'] = [ yield_curve.zero_rate(item) 
    for item in vix_option_data['TTM'] ]



    #filename = "MC.txt"

    print 333


    # Calculte the model prices of VIX options
    paras = {"a" : 33.0, "b" : -0.9, "c" : 0.0017} 
    dynamic_local_vol.cal_dynamic_vix(paras)
    calibrate.cal_vix_options(vix_option_data, dynamic_local_vol)
  


    MSE = calibrate.cal_implied_vol(vix, vix_option_data)
    print paras, MSE
    print vix_option_data
    calibrate.plot_implied_vol(vix_option_data)



























   
    #paras = {"a" : 12, "b" : 8, "c" : 0.0001}



    




