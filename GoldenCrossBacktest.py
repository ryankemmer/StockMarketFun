import numpy as np
import math
import bs4 as bs
import requests
import yfinance as yf
import pandas as pd
import datetime
from collections import OrderedDict

def MovingAverage(df, window):
    avg = df.Close.rolling(window, min_periods=1).mean()
    return avg

def ExponentialMovingAverage(df, window):
    avg = df.Close.ewm(span=window, adjust=False).mean()
    return avg


def stochastics(dataframe, low, high, close, k, d):

    df = dataframe.copy()

    # Set minimum low and maximum high of the k stoch
    low_min  = df[low].rolling( window = k ).min()
    high_max = df[high].rolling( window = k ).max()

    # Fast Stochastic
    df['k_fast'] = 100 * (df[close] - low_min)/(high_max - low_min)
    df['d_fast'] = df['k_fast'].rolling(window = d).mean()

    # Slow Stochastic
    df['k_slow'] = df["d_fast"]
    df['d_slow'] = df['k_slow'].rolling(window = d).mean()

    return df



def backtest_with_stop_loss(ticker, startdate, enddate, capital, interval = "60m"):

    #get historical data
    data = yf.download(ticker,startdate, enddate, interval= interval)

    #get volitility
    returns = np.log(data['Close']/data['Close'].shift())
    returns.fillna(0, inplace=True)
    volatilities = returns.rolling(window=100).std()*np.sqrt(100)

    #get moving averages, dates, and prices
    MA_50 = MovingAverage(data,50)
    MA_200 = MovingAverage(data,200) 
    datetimes = data.index.to_numpy()
    prices = data.Close.to_numpy()

    #set initial spending balance
    balance = capital
    net_assets = capital
    portfolio = OrderedDict()
    stops = OrderedDict()
    log = OrderedDict()
    prevOrder = None

    for i, date in enumerate(datetimes):

            if i > 0:

                #check if stop condition is met
                if len(portfolio) > 0:
                    if prevOrder == 'buy':

                        current_price = prices[i]
                        stop_loss = list(stops.items())[-1][1]

                        if current_price < stop_loss:

                            shares_sell = portfolio[ticker]  
                            log[date] = 'Sold for ' + str(prices[i]) + 'due to stop criteria being met'
                            prevOrder = 'sell'

                            #update balance
                            balance = balance + (shares_sell * prices[i])

                #if previously the 200 day moving average is greater than the 50 day
                if MA_200[i - 1] > MA_50[i - 1]:

                    #if a golden cross occurs
                    if MA_50[i] >= MA_200[i]:
                        
                        #calculate max shares availible
                        max_shares = math.floor(balance / prices[i])
                        stop_loss = prices[i] - (prices[i] * volatilities[i])

                        portfolio[ticker] = max_shares
                        stops[ticker] = stop_loss
                        log[date] = 'Bought for: ' + str(prices[i]) + 'with stoploss: ' + str(stop_loss)
                        prevOrder = 'buy'

                        balance = balance - (max_shares * prices[i])

                #if previously the 50 day moving average is greater than the 200 day
                if MA_50[i - 1] > MA_200[i - 1]:

                    #if a death cross occurs
                    if MA_200[i] >= MA_50[i]:

                        #determine shares to sell (sell all)
                        if len(portfolio) > 0:
                            if prevOrder == 'buy':
                                shares_sell = portfolio[ticker]  
                                log[date] = 'Sold for ' + str(prices[i])
                                prevOrder = 'sell'

                                #update balance
                                balance = balance + (shares_sell * prices[i])

    #TODO: Fix bug here
    net_assets = (portfolio[ticker] * prices[-1]) + balance #most recent value of stocks and cash together
    cumreturns =  ((net_assets -  capital) / capital) * 100

    return cumreturns, portfolio, log

def backtest(ticker, startdate, enddate, capital, interval = "60m"):

    #get historical data
    data = yf.download(ticker,startdate, enddate, interval= interval)

    #get moving averages, dates, and prices
    MA_50 = MovingAverage(data,50)
    MA_200 = MovingAverage(data,200) 
    datetimes = data.index.to_numpy()
    prices = data.Close.to_numpy()

    #set initial spending balance
    balance = capital
    net_assets = capital
    portfolio = {}
    log = {}

    for i, date in enumerate(datetimes):

        if i > 0:
            
            #if previously the 200 day moving average is greater than the 50 day
            if MA_200[i - 1] > MA_50[i - 1]:

                #if a golden cross occurs
                if MA_50[i] >= MA_200[i]:
                    
                    #calculate max shares availible
                    max_shares = math.floor(balance / prices[i])

                    portfolio[ticker] = max_shares
                    log[date] = 'Bought for ' + str(prices[i])

                    balance = balance - (max_shares * prices[i])

            #if previously the 50 day moving average is greater than the 200 day
            if MA_50[i - 1] > MA_200[i - 1]:

                #if a death cross occurs
                if MA_200[i] >= MA_50[i]:

                    #determine shares to sell (sell all)
                    if len(portfolio) > 0:
                        shares_sell = portfolio[ticker]  
                        log[date] = 'Sold for ' + str(prices[i])

                        #update balance
                        balance = balance + (shares_sell * prices[i])

    #TODO: Fix bug here
    net_assets = (portfolio[ticker] * prices[-1]) + balance #most recent value of stocks and cash together
    cumreturns =  ((net_assets -  capital) / capital) * 100

    return cumreturns, portfolio, log


def hold(ticker, startdate, enddate, capital, interval = "60m"):

    #get historical data
    data = yf.download(ticker,startdate, enddate, interval= interval)
    prices = data.Open.to_numpy()

    balance = capital
    max_shares = math.floor(balance / prices[0])

    #buy
    balance = balance - (max_shares * prices[0])
    #sell
    balance = balance + (max_shares * prices[-1])

    cumreturns =  ((balance -  capital) / capital) * 100
    print(cumreturns)

    return cumreturns

def get_smp500_tickers():

    resp = requests.get('http://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    soup = bs.BeautifulSoup(resp.text, 'lxml')
    table = soup.find('table', {'class': 'wikitable sortable'})
    tickers = []
    for row in table.findAll('tr')[1:]:
        ticker = row.findAll('td')[0].text
        tickers.append(ticker)

    tickers = [s.replace('\n', '') for s in tickers]

    return tickers

if __name__ == '__main__':

    tickers = get_smp500_tickers()

    start_time = datetime.datetime(2020, 9, 2)
    end_time = datetime.datetime.now().date().isoformat()

    results = pd.DataFrame(columns = ['Stock', 'Holding Returns', 'Golden Cross Returns', 'Golden Cross With Stop Loss'])

    for ticker in tickers:

        try:
            returns, portfolio, log = backtest(ticker,start_time,end_time, 1000, "1h")
            returns2, portfolio2, log2 = backtest_with_stop_loss(ticker,start_time,end_time, 1000, "1h")
            holding_returns = hold(ticker,start_time,end_time, 1000, "1h")

            results = results.append({'Stock' : ticker, 'Holding Returns' : holding_returns, 'Golden Cross Returns' : returns, 'Golden Cross With Stop Loss': returns2}, ignore_index = True)

        except:
            pass


        results.to_csv('res.csv')