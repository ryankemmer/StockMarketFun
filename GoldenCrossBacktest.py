import numpy as np
import math
import yfinance as yf
import datetime

def MovingAverage(df, window):
    avg = df.Open.rolling(window, min_periods=1).mean()
    return avg

def ExponentialMovingAverage(df, window):
    avg = df.Open.ewm(span=window, adjust=False).mean()
    return avg

def backtest(ticker, startdate, enddate, capital, interval = "60m"):

    #get historical data
    data = yf.download(ticker,startdate, enddate, interval= interval)

    #get moving averages, dates, and prices
    MA_50 = MovingAverage(data,50)
    MA_200 = MovingAverage(data,200) 
    datetimes = data.index.to_numpy()
    prices = data.Open.to_numpy()

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
                    shares_sell = portfolio[ticker]  
                    log[date] = 'Sold for ' + str(prices[i])

                    #update balance
                    balance = balance + (shares_sell * prices[i])


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

    return cumreturns
    

if __name__ == '__main__':

    start_time = datetime.datetime(2020, 9, 2)
    end_time = datetime.datetime.now().date().isoformat()

    returns, portfolio, log = backtest('AAPL',start_time,end_time, 1000, "1h")
    holding_returns= hold('AAPL',start_time,end_time, 1000, "1h")

    print(returns)
    print(holding_returns)
    print(portfolio)
    print(log)