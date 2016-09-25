# volatility.py

import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
from collections import defaultdict
from mpl_toolkits.mplot3d import Axes3D
from scipy.interpolate import interp1d
from QuantLib import *


class VolatilitySurface(object):

    def __init__(self, evaluation_date, maturity_dates, strikes,
        implied_vol_matrix, spot, yield_curve,  dividend_curve):
        self.implied_vol_surface = {}
        self.local_vol_surface = {}
        self.create_surface(evaluation_date, maturity_dates, strikes,
        implied_vol_matrix, spot, yield_curve,  dividend_curve)


    def create_surface(self, evaluation_date, maturity_dates, strikes,
        implied_vol_matrix, spot, yield_curve,  dividend_curve):

        calendar = TARGET()
        day_counter = ActualActual()
        evaluation_date_ql = self._date_to_ql(evaluation_date)
        maturity_dates_ql = np.array([self._date_to_ql(date) 
            for date in maturity_dates])
           
        nrows, ncols = implied_vol_matrix.shape
        implied_vol_matrix_ql = Matrix(nrows, ncols)
        for i in range(0, nrows):
            for j in range(0, ncols):
                implied_vol_matrix_ql[i][j] = implied_vol_matrix[i][j]

        self.implied_vol_surface = BlackVarianceSurface(evaluation_date_ql, 
            calendar, maturity_dates_ql, strikes, 
            implied_vol_matrix_ql, day_counter)

        self.local_vol_surface = LocalVolSurface(
            BlackVolTermStructureHandle(self.implied_vol_surface), 
            YieldTermStructureHandle(yield_curve.curve), 
            YieldTermStructureHandle(dividend_curve.curve), spot)


    def surface_plot(self, strikes, time_to_maturities, file_path):

        strike_matrix, ttm_matrix = np.meshgrid(strikes, time_to_maturities) 
        implied_vol_matrix = np.zeros((len(time_to_maturities), len(strikes)))
            # (time_to_maturity, strike)
        for i in range(0, len(strikes)):
            for j in range(0, len(time_to_maturities)):
                implied_vol_matrix[j][i] = self.implied_vol_surface.blackVol(
                    time_to_maturities[j], strikes[i])

        fig = plt.figure(figsize = (8, 12))

        ax = fig.add_subplot(2, 1, 1, projection = '3d')
        surf = ax.plot_surface(strike_matrix, ttm_matrix, 
            implied_vol_matrix,
            rstride = 1, cstride = 1, alpha = 0.65,
            cmap = plt.cm.jet, #plt.cm.coolwarm,
            linewidth = 0.5, antialiased = True)
        ax.set_xlabel('strike')
        ax.set_ylabel('time-to-maturity')
        ax.set_zlabel('implied volatility')
        fig.colorbar(surf, shrink = 0.6) #aspect = 1)

        local_vol_matrix = np.zeros((len(time_to_maturities), len(strikes)))
        for i in range(0, len(strikes)):
            for j in range(0, len(time_to_maturities)):
                try:
                    local_vol_matrix[j][i] = self.local_vol_surface.localVol(
                        time_to_maturities[j], strikes[i])
                except:
                    print(1111)

        ax = fig.add_subplot(2, 1, 2, projection = '3d')
        surf = ax.plot_surface(strike_matrix, ttm_matrix, local_vol_matrix,
            rstride = 1, cstride = 1, alpha = 0.65,
            cmap = plt.cm.jet, #plt.cm.coolwarm,
            linewidth = 0.5, antialiased = True)
        ax.set_xlabel('strike')
        ax.set_ylabel('time-to-maturity')
        ax.set_zlabel('local volatility')
        fig.colorbar(surf, shrink = 0.6) #aspect = 5)

        plt.tight_layout()
        if os.path.exists(file_path):
          os.remove(file_path)
        plt.savefig(file_path)


    def _date_to_ql(self, date):
        return Date(date.day, date.month, date.year)


class DynamicLocalVolSurface(object):

    def __init__(self, volatility_surface, spot, yield_curve,  
        dividend_curve, months = 3, grids_per_month = 1, 
        deltax_per_month = 0.3):

        self.spot = spot 
        self.yield_curve = yield_curve
        self.dividend_curve = dividend_curve
        self.volatility_surface = volatility_surface

        self.dynamic_vix = {}

        self.create_local_var_tree(months, grids_per_month, deltax_per_month)


    def create_local_var_tree(self, months = 3, grids_per_month = 1, 
        deltax_per_month = 0.3):    

        ncols = months * grids_per_month + 1
        nrows = months * grids_per_month * 2 + 1
        self.deltat = 1.0 / 12.0 / grids_per_month
        self.deltax = deltax_per_month / grids_per_month
        self.A =  self.deltat / 2.0 / self.deltax ** 2
        self.B = self.deltat / 2.0 / self.deltax
        self.vix_steps = 3 * grids_per_month

        strikes = np.linspace(- (ncols - 1) * self.deltax, 
            (ncols - 1) * self.deltax, nrows)
        strikes = np.exp(strikes) * self.spot
        time_to_maturities = np.linspace(0.0, months / 12.0 , ncols)     

        self.local_var_tree = pd.DataFrame(np.zeros((nrows, ncols)), 
            index = strikes, columns = time_to_maturities)
        for j in range(0, ncols):
            for i in range(ncols - j - 1, ncols + j):
                try:
                    self.local_var_tree.iloc[i, j] = \
                        self.volatility_surface.local_vol_surface.localVol(
                        time_to_maturities[j], strikes[i], True) ** 2
                except:
                    self.local_var_tree.iloc[i, j] = \
                        self.local_var_tree.iloc[i - 1, j]

        



    def cal_dynamic_vix(self, paras):
        self.dynamic_vix = defaultdict(list)
        self._cal_dynamic_vix(paras, self.local_var_tree, 1.0)

        #print(self.dynamic_vix)


    def _cal_dynamic_vix(self, paras, local_var_tree, prob0):
        time_to_maturities = local_var_tree.columns
        strikes = local_var_tree.index
        ncols = len(time_to_maturities)
        nrows = len(strikes)

        prob_tree = np.zeros((nrows, ncols))
        self._build_prob_tree(prob_tree, local_var_tree)
        
        #print local_var_tree.iloc[::-1]
        #print

        vix_est = 0.0
        for j in range(0, self.vix_steps):
            for i in range(ncols - j - 1, ncols + j):
                #print prob_tree[i][j], local_var_tree.iloc[i, j]
                vix_est += prob_tree[i][j] * local_var_tree.iloc[i, j]
        vix_est = np.sqrt(vix_est * self.deltat / 0.25) * 100.0
        self.dynamic_vix[time_to_maturities[0]].append((prob0, vix_est))

        #print vix_est

        if (ncols <= self.vix_steps + 1):
           return 

        local_var_tree_up = local_var_tree.copy()
        local_var_tree_down = local_var_tree.copy()
        for j in range(0, ncols - 1):
            for i in range(ncols + j - 1, ncols - j - 2, -1):

                #print j ,i 
                beta = paras['a'] * np.exp(-paras['b'] \
                    * (time_to_maturities[j] - time_to_maturities[0]) \
                    - paras['c'] * strikes[i])
                drift = (- beta ** 2 / 2.0) * self.deltat 
                diffusion = beta * np.sqrt(self.deltat)              
                alpha = np.log(2.0 / (np.exp(drift + diffusion) \
                    + np.exp(drift - diffusion))) / self.deltat

                drift += alpha * self.deltat

                local_var_tree_up.iloc[i, j] *= np.exp(drift + diffusion) 
                local_var_tree_down.iloc[i, j] *= np.exp(drift - diffusion)


        prob_tree_up = np.zeros((nrows, ncols))
        prob_tree_down = np.zeros((nrows, ncols))
        self._build_prob_tree(prob_tree_up, local_var_tree_up)
        self._build_prob_tree(prob_tree_down, local_var_tree_down)
        


        local_var_tree_up_up = local_var_tree_up.iloc[2:, 1:]
        self._cal_dynamic_vix(paras, local_var_tree_up_up, 
            prob_tree[ncols][1] * prob0 / 2.0)
        local_var_tree_up_mid = local_var_tree_up.iloc[1:(nrows - 1), 1:]
        self._cal_dynamic_vix(paras, local_var_tree_up_mid, 
            prob_tree[ncols - 1][1] * prob0 / 2.0)
        local_var_tree_up_down = local_var_tree_up.iloc[:(nrows - 2), 1:]
        self._cal_dynamic_vix(paras, local_var_tree_up_down, 
            prob_tree[ncols - 2][1] * prob0 / 2.0)
        

        local_var_tree_down_up = local_var_tree_down.iloc[2:, 1:]
        self._cal_dynamic_vix(paras, local_var_tree_down_up, 
            prob_tree[ncols][1] * prob0 / 2.0)
        local_var_tree_down_mid = local_var_tree_down.iloc[1:(nrows - 1), 1:]
        self._cal_dynamic_vix(paras, local_var_tree_down_mid, 
            prob_tree[ncols - 1][1] * prob0 / 2.0)
        local_var_tree_down_down = local_var_tree_down.iloc[:(nrows - 2), 1:]
        self._cal_dynamic_vix(paras, local_var_tree_down_down, 
            prob_tree[ncols - 2][1] * prob0 / 2.0)     





    def _build_prob_tree(self, prob_tree, local_var_tree):

        time_to_maturities = local_var_tree.columns
        strikes = local_var_tree.index
        ncols = len(time_to_maturities)
        nrows = len(strikes)

        yield_rates = [ self.yield_curve.zero_rate(item) 
            for item in time_to_maturities ]
        dividend_rates = [ self.dividend_curve.zero_rate(item) 
            for item in time_to_maturities ]

        prob_tree[ncols - 1, 0] = 1.0
        for j in range(0, ncols - 1):
            for i in range(ncols - j - 1, ncols + j):
                rates_diff = yield_rates[j] - dividend_rates[j]
                prob_up = local_var_tree.iloc[i, j] * self.A \
                    + self.B * rates_diff
                prob_down = prob_up - 2.0 * self.B * rates_diff
                prob_mid = 1.0 - prob_up - prob_down
                prob_tree[i + 1][j + 1] += prob_tree[i][j] * prob_up
                prob_tree[i][j + 1] += prob_tree[i][j] * prob_mid
                prob_tree[i - 1][j + 1] += prob_tree[i][j] * prob_down
                




    def cal_vix_option(self, time_to_maturity, strike):
   

        time_to_maturities = self.dynamic_vix.keys()
        prices = [ np.sum([item[0] * np.max((item[1] - strike, 0)) 
            for item in value ])
            for value in self.dynamic_vix.values() ]

        f = interp1d(time_to_maturities, prices)



        return f(time_to_maturity)


