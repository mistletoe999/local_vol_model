# data.py

import datetime as dt
import numpy as np
import matplotlib.pyplot as plt
import os
import pandas as pd
import pandas_datareader.data as web
import pickle
import statsmodels.api as sm
import Quandl


class DataHandler(object):
	"""Class for downloading and importing data.

	.. _Google Python Style Guide:
		http://google.github.io/styleguide/pyguide.html

	Attributes:
		liborChain (pandas.DataFrame): Market data of LIBOR and LIBOR swaps. 
		SPXHist (pandas.DataFrame): SPX time series.
		VIXHist (pandas.DataFrame): VIX time series.
		SPXOptionsChain (pandas.DataFrame): Market data of SPX options. 
		VIXOptionsChain (pandas.DataFrame): Market data of VIX options.
		


	"""


	def __init__(self, startDate = None, evaluationDate = None):
		if startDate is None:
			self.startDate = dt.datetime(2000, 1, 1)
		else:
			self.startDate = startDate

		if evaluationDate is None:
			self.evaluationDate = dt.datetime.date(dt.datetime.now())
		else:
			self.evaluationDate = evaluationDate
			
		self.liborChain = {}
		self.SPXHist = {}
		self.VIXHist = {}
		self.SPXOptionsChain = {}
		self.VIXOptionsChain = {}

		if os.path.exists('../data_graphs/LIBOR.dat'):
			self.liborImporter()
		else:
			self.liborDownloader() 
			
		if os.path.exists('../data_graphs/SPX.dat'):
			self.SPXImporter()
		else:
			self.SPXDownloader() 
			
		if os.path.exists('../data_graphs/VIX.dat'):
			self.VIXImporter() 
		else:
			self.VIXDownloader()
	
		if os.path.exists('../data_graphs/SPXOptions.dat'):
			self.SPXOptionsImporter()
		else:
			self.SPXOptionsDownloader() 

		if os.path.exists('../data_graphs/VIXOptions.dat'):
			self.VIXOptionsImporter() 
		else:
			self.VIXOptionsDownloader()

		print "Data has been imported..." 

	def liborDownloader(self):

		liborHist = Quandl.get([ 'FRED/USD1WKD156N', 
								 'FRED/USD1MTD156N', 'FRED/USD3MTD156N', 
								 'FRED/USD6MTD156N','FRED/USD12MD156N', 
								 'FRED/DSWP2', 'FRED/DSWP3', 'FRED/DSWP5',
								 'FRED/DSWP7', 'FRED/DSWP10', 'FRED/DSWP30'], 
								trim_start = self.evaluationDate - dt.timedelta(10), 
								trim_end = self.evaluationDate,
								authtoken = 'g1JT2dTM4BpHaC58aMaT')
		liborHist = liborHist.fillna(method = 'ffill')
		
		self.liborChain = pd.DataFrame({'Rates' : liborHist.ix[-1]})
		index = ['libor1w', 'libor1m', 'libor3m', 'libor6m', 'libor1y', 
			'swap2y', 'swap3y', 'swap5y', 'swap7y', 'swap10y', 'swap30y']
		self.liborChain.index = index
 		
		file = open('../data_graphs/LIBOR.dat', 'w')
		pickle.dump(self.liborChain, file)
		file.close()

	def SPXDownloader(self):
		self.SPXHist = web.DataReader('^GSPC', 'yahoo', self.startDate, self.evaluationDate)
		file = open('../data_graphs/SPX.dat', 'w')
		pickle.dump(self.SPXHist, file)
		file.close()

	def VIXDownloader(self):
		self.VIXHist = web.DataReader('^VIX', 'yahoo', self.startDate, self.evaluationDate)
		file = open('../data_graphs/VIX.dat', 'w')
		pickle.dump(self.VIXHist, file)
		file.close()

	def SPXOptionsDownloader(self):
		""" Download SPX Options data from yahoo via pandas

		.. _pandas:
			http://pandas.pydata.org/pandas-docs/stable/remote_data.html#yahoo-finance-options
		"""
		SPX = web.Options('^SPX', 'yahoo')
		self.SPXOptionsChain = SPX.get_all_data()
		file = open('../data_graphs/SPXOptions.dat', 'w')
		pickle.dump(self.SPXOptionsChain, file)
		file.close()

	def VIXOptionsDownloader(self):
		VIX = web.Options('^VIX', 'yahoo')
		self.VIXOptionsChain = VIX.get_all_data()
		file = open('../data_graphs/VIXOptions.dat', 'w')
		pickle.dump(self.VIXOptionsChain, file)
		file.close()

	def liborImporter(self):
		file = open('../data_graphs/LIBOR.dat', 'r')
		self.liborChain = pickle.load(file)
		file.close()

	def SPXImporter(self):
		file = open('../data_graphs/SPX.dat', 'r')
		self.SPXHist = pickle.load(file)
		file.close()

	def VIXImporter(self):
		file = open('../data_graphs/VIX.dat', 'r')
		self.VIXHist = pickle.load(file)
		file.close()

	def SPXOptionsImporter(self):
		file = open('../data_graphs/SPXOptions.dat', 'r')
		self.SPXOptionsChain = pickle.load(file)
		file.close()

	def VIXOptionsImporter(self):
		file = open('../data_graphs/VIXOptions.dat', 'r')
		self.VIXOptionsChain = pickle.load(file)
		file.close()

	def SPXVIXPlot(self, startDate, endDate):
		"""Plot the time series of SPX and VIX, and the scatter of their returns. 

		Args:
			startDate (datetime.datetime): Startdate.
			endDate (datetime.datetime): Enddate.

		"""
		startDate = pd.Timestamp(startDate)
		endDate = pd.Timestamp(endDate)
		SPXIndex = (startDate < self.SPXHist.index) & (self.SPXHist.index < endDate)
		VIXIndex = (startDate < self.VIXHist.index) & (self.VIXHist.index < endDate)
		SPXVIXHist = pd.DataFrame({
			'SPX': self.SPXHist['Close'][SPXIndex],
			'VIX': self.VIXHist['Close'][VIXIndex]})
		SPXVIXHist.fillna(method = 'ffill')
		
		
		plt.figure()
		SPXVIXHist.plot(subplots = True, grid = True, 
			style = 'b', figsize = (8, 8), colormap=plt.cm.jet)
		plt.xlabel('date')
		plt.tight_layout()
		if os.path.exists('../data_graphs/spx_vix_time_series.pdf'):
			os.remove('../data_graphs/spx_vix_time_series.pdf')
		plt.savefig('../data_graphs/spx_vix_time_series.pdf')

		plt.figure()
		SPXVIXReturn = np.log(SPXVIXHist / SPXVIXHist.shift(1))
		SPXVIXReturn = SPXVIXReturn.ix[1:]
		xDat = SPXVIXReturn['SPX']
		yDat = SPXVIXReturn['VIX'] 
		model = sm.OLS(yDat, xDat)
		#model = sm.OLS(yDat, add_constant(xDat))
		#xAjdDat = xDat[(xDat < 0.05)][(xDat > -0.05)]
		#yAdjDat = yDat[(xDat < 0.05)][(xDat > -0.05)]
		#model = sm.OLS(yAdjDat, xAjdDat)
		res = model.fit()
		#print res.summary()

		plt.plot(xDat, yDat, 'r.')
		ax = plt.axis()
		x = np.linspace(ax[0], ax[1] - 0.00001)
		yPred = res.predict(x)
		plt.plot(x, yPred, 'b', lw = 2)
		plt.grid(True)
		plt.xlabel('SPX returns')
		plt.ylabel('VIX returns')
		if os.path.exists('../data_graphs/spx_vix_returns.pdf'):
			os.remove('../data_graphs/spx_vix_returns.pdf')
		plt.savefig('../data_graphs/spx_vix_returns.pdf')
		
		
	def printData(self):
		print self.liborChain
		print self.SPXHist.tail()
		print self.VIXHist.tail()
		#print self.SPXOptionsChain
		#print self.VIXOptionsChain
