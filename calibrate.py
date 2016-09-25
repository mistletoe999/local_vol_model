# calibrate.py

import datetime as dt
import matplotlib.pyplot as plt
import numpy as np
import os

import bsm_formula

def cal_implied_vol(vix, vix_option_data):

    
    vix_option_data['Mid'] = (vix_option_data['Bid'] 
        + vix_option_data['Ask']) / 2.0

    vix_option_data['ImpliedMid'] = [ bsm_formula.bsm_call_imp_vol(
        vix, item['Strike'], item['TTM'], item['ZeroRate'], 
        item['ZeroRate'], item['Mid'], 1.5)
        for index, item in vix_option_data.iterrows() ]


    vix_option_data['ImpliedBid'] = [ bsm_formula.bsm_call_imp_vol(
        vix, item['Strike'], item['TTM'], item['ZeroRate'], 
        item['ZeroRate'], item['Bid'], 1.5)
        for index, item in vix_option_data.iterrows() ]


    vix_option_data['ImpliedAsk'] = [ bsm_formula.bsm_call_imp_vol(
        vix, item['Strike'], item['TTM'], item['ZeroRate'], 
        item['ZeroRate'], item['Ask'], 1.5)
        for index, item in vix_option_data.iterrows() ]

    vix_option_data['ImpliedModel'] = [ bsm_formula.bsm_call_imp_vol(
        vix, item['Strike'], item['TTM'], item['ZeroRate'], 
        item['ZeroRate'], item['Model'], 1.5)
        for index, item in vix_option_data.iterrows() ]

    MSE = np.average(((vix_option_data['Mid'] - vix_option_data['Model']) 
        / vix_option_data['Mid']) ** 2)
    #print MSE
    return MSE

def plot_implied_vol(vix_option_data):

    vix_option_data_grouped = vix_option_data.groupby('Maturity')
    #print vix_option_data_grouped

    nrows = (vix_option_data_grouped.ngroups + 1) / 2        

    fig, axes = plt.subplots(figsize=(12, 6 * nrows), 
        nrows = nrows, ncols = 2,     
        gridspec_kw = dict(hspace = 0.4)) 
    
    volatilites = np.array(vix_option_data.iloc[:, -4:])
    ylimits = [np.min(volatilites) - 0.1, np.max(volatilites) + 0.1]

    targets = zip(vix_option_data_grouped.groups.keys(), axes.flatten())
    for i, (key, ax) in enumerate(targets):
        data = vix_option_data_grouped.get_group(key)
        #print data
        ax.plot(data['Strike'], data['ImpliedBid'], '-.')
        ax.plot(data['Strike'], data['ImpliedAsk'], ':')
        ax.plot(data['Strike'], data['ImpliedMid'], '--')
        ax.plot(data['Strike'], data['ImpliedModel'], lw = 3)
        xlimits = [np.min(data['Strike']) - 0.2, np.max(data['Strike']) + 0.2]
        ax.set_xlim(xlimits)
        ax.set_ylim(ylimits)
        ax.set_xlabel('strike')
        ax.set_ylabel('implied volatility')
        ax.grid(True)
        date = key.astype('M8[D]').astype(np.datetime64)
        ax.set_title(date)
        ax.legend(labels = ['Bid', 'Ask', 'Mid', 'Model'])

    file_path = '../data_graphs/vix_implied_vol_skew.pdf'
    if os.path.exists(file_path):
          os.remove(file_path)
    plt.savefig(file_path, bbox_inches='tight')


def cal_vix_options(vix_option_data, dynamic_local_vol):


    vix_option_data['Model'] = [ dynamic_local_vol.cal_vix_option(
        item['TTM'], item['Strike'])
        for index, item in vix_option_data.iterrows() ]

    print 