# curves.py

import matplotlib.pyplot as plt
import numpy as np
import os
from QuantLib import *


class YieldCurve(object):

	def __init__(self, liborChain):
		self.depoSwapCurve = {}
		self.createCurve(liborChain)
		

	def createCurve(self, liborChain):

		calendar = TARGET()
		todaysDate = Date(22, April, 2016);
		Settings.instance().evaluationDate = todaysDate
		settlementDate = Date(22, April, 2016)

		rates = liborChain['Rates'] / 100.0

		# market quotes
		deposits = { (1, Weeks) : rates[0],
					 (1, Months) : rates[1],
					 (3, Months) : rates[2],
					 (6, Months) : rates[3],
					 (9, Months) : (rates[3] + rates[4]) / 2,
					 (1, Years) : rates[4] }


		swaps = { (2, Years) : rates[5],
				  (3, Years) : rates[6],
				  (5, Years) : rates[7],
				  (7, Years) : rates[8],
				  (10, Years) : rates[9],
				  (30, Years) : rates[10] }

		# convert them to Quote objects
		for n, unit in deposits.keys():
			deposits[(n, unit)] = SimpleQuote(deposits[(n, unit)])
		for n,unit in swaps.keys():
			swaps[(n,unit)] = SimpleQuote(swaps[(n, unit)])

		# build rate helpers

		dayCounter = Actual360()
		settlementDays = 2
		depositHelpers = [ DepositRateHelper(QuoteHandle(deposits[(n, unit)]),
				Period(n,unit), settlementDays, calendar, ModifiedFollowing,
				False, dayCounter)
			for n, unit in [(1, Weeks), (1, Months), (3, Months),
			                (6, Months), (9, Months), (1, Years)] ]

		settlementDays = 2
		fixedLegFrequency = Annual
		fixedLegTenor = Period(1, Years)
		fixedLegAdjustment = Unadjusted
		fixedLegDayCounter = Thirty360()
		floatingLegFrequency = Semiannual
		floatingLegTenor = Period(6, Months)
		floatingLegAdjustment = ModifiedFollowing
		swapHelpers = [ SwapRateHelper(QuoteHandle(swaps[(n, unit)]),
				Period(n,unit), calendar, fixedLegFrequency,
				fixedLegAdjustment, fixedLegDayCounter, Euribor6M())             
			for n, unit in swaps.keys() ]


		# term-structure construction
		helpers = depositHelpers + swapHelpers
		self.depoSwapCurve = PiecewiseFlatForward(settlementDate, helpers,
			Actual360())


	def discountFactor(self, timeToMty):
		return self.depoSwapCurve.discount(timeToMty)


	def instForwardRate(self, timeToMty, delta = 0.001):
		return self.depoSwapCurve.forwardRate(timeToMty, timeToMty + delta, 
			Continuous, Daily).rate() 


	def discountCurve(self):
		timeToMty = np.concatenate([np.linspace(0, 2, 100), np.linspace(2, 30, 200)[1:]])
		discount = [self.discountFactor(tau) for tau in timeToMty]
		
		plt.figure()
		plt.plot(timeToMty, discount, 'r', lw = 2)
		plt.grid(True)
		plt.xlabel('Time to Maturity')
		plt.ylabel('Discount Factor')
		if os.path.exists('../data_graphs/discount_factor.pdf'):
			os.remove('../data_graphs/discount_factor.pdf')
		plt.savefig('../data_graphs/discount_factor.pdf')


	def instForwardRateCurve(self):
		timeToMty = np.concatenate([np.linspace(0, 2, 100), np.linspace(2, 11, 400)[1:],
			np.linspace(11, 30, 100)[1:]])
		rate = [self.instForwardRate(tau) for tau in timeToMty]
		
		plt.figure()
		plt.plot(timeToMty, rate, 'r', lw = 2)
		plt.grid(True)
		plt.xlabel('Time to Maturity')
		plt.ylabel('Instantaneous Forward Rate')
		if os.path.exists('../data_graphs/forward_rate.pdf'):
			os.remove('../data_graphs/forward_rate.pdf')
		plt.savefig('../data_graphs/forward_rate.pdf')



class ZeroRateCurve(object):


    def __init__(self, evaluation_date, maturity_dates, zero_rates):
        self.curve = {}
        self.create_curve(evaluation_date, maturity_dates, zero_rates)


    def create_curve(self, evaluation_date, maturity_dates, zero_rates):
        
        calendar = TARGET()
        day_counter = ActualActual()
        evaluation_date_ql = self._date_to_ql(evaluation_date)
        maturity_dates_ql = np.append(evaluation_date_ql,
            [self._date_to_ql(date) for date in maturity_dates])
        zero_rates = np.append(zero_rates[0], zero_rates) 
        self.curve = ZeroCurve(maturity_dates_ql, zero_rates, 
            day_counter, calendar)


    def zero_rate(self, time_to_maturity):
        return self.curve.forwardRate(0, 
            time_to_maturity, Continuous, Daily).rate() 

    def inst_forward_rate(self, time_to_maturity, delta = 0.0001):
        return self.curve.forwardRate(time_to_maturity, 
            time_to_maturity + delta, Continuous, Daily).rate() 

    def zero_curve_plot(self, time_to_maturities, xlabel, ylabel, file_path):
        
        zero_rates = [self.zero_rate(item) for item \
            in time_to_maturities]

        plt.figure()
        plt.plot(time_to_maturities, zero_rates, 'r', lw = 2)
        plt.grid(True)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        if os.path.exists(file_path):
            os.remove(file_path)
        plt.savefig(file_path)
     

    def inst_forward_rate_plot(self, time_to_maturities, xlabel, ylabel, 
        file_path):
        
        inst_forward_rates = [self.inst_forward_rate(item) for item \
            in time_to_maturities]

        plt.figure()
        plt.plot(time_to_maturities, inst_forward_rates, 'r', lw = 2)
        plt.grid(True)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        if os.path.exists(file_path):
            os.remove(file_path)
        plt.savefig(file_path)


    def _date_to_ql(self, date):
        return Date(date.day, date.month, date.year)
        

