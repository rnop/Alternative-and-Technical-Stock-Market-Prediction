import quandl
import pandas as pd
import numpy as np
import pickle
import yfinance
import requests
import xgboost as xgb

def get_alternative_data():
    aaii = quandl.get("AAII/AAII_SENTIMENT", authtoken="xvRAkcY8ExMFtqF9fEK4")
    aaii = aaii[['Bullish','Neutral','Bearish']].pct_change().dropna()
    aaii = aaii[['Bullish','Neutral','Bearish']]
    aaii = aaii.resample('d').ffill().dropna()
    aaii_days = ((aaii.tail(1).index  - pd.datetime.today()).days[0]*-1) - 1
    aaii = aaii.append([aaii.tail(1)]*aaii_days)
    aaii_index = pd.date_range('1987/07/31', pd.datetime.today())
    aaii = aaii.set_index(aaii_index)

    bigmac = quandl.get("ECONOMIST/BIGMAC_USA", authtoken="xvRAkcY8ExMFtqF9fEK4")
    bigmac = bigmac['local_price'].pct_change().dropna()
    bigmac = pd.DataFrame(bigmac.resample('d').ffill().dropna())
    bigmac_days = ((bigmac.tail(1).index  - pd.datetime.today()).days[0]*-1) - 1
    bigmac = bigmac.append([bigmac.tail(1)]*bigmac_days)
    bigmac_index = pd.date_range('2001-04-30', pd.datetime.today())
    bigmac = bigmac.set_index(bigmac_index)

    eureka = quandl.get("EUREKA/MEI27", authtoken="xvRAkcY8ExMFtqF9fEK4")
    eureka = eureka['Returns'].pct_change().dropna()
    eureka = pd.DataFrame(eureka.resample('d').ffill().dropna())
    eureka_days = ((eureka.tail(1).index  - pd.datetime.today()).days[0]*-1) - 1
    if eureka_days > 0:
        eureka = eureka.append([eureka.tail(1)]*(eureka_days))
        eureka_index = pd.date_range('2010-09-30', pd.datetime.today())
        eureka = eureka.set_index(eureka_index)

    misery = quandl.get("USMISERY/INDEX", authtoken="xvRAkcY8ExMFtqF9fEK4")
    misery = misery[['Unemployment Rate','Inflation Rate','Misery Index']].pct_change().dropna()
    misery = misery[['Unemployment Rate','Inflation Rate','Misery Index']]
    misery = misery.resample('d').ffill().dropna()
    misery_days = ((misery.tail(1).index  - pd.datetime.today()).days[0]*-1) - 1
    misery = misery.append([misery.tail(1)]*misery_days)
    misery_index = pd.date_range('1948-02-29', pd.datetime.today())
    misery = misery.set_index(misery_index)
    
    alternative_data = eureka.join(misery).join(bigmac).join(aaii)
    alternative_data.replace([np.inf, -np.inf], np.nan, inplace=True)
    alternative_data.dropna(inplace=True)
    alternative_data.index.name = 'Date'
    alternative_data.to_csv("data/cleaned_alternative_data.csv")
    return alternative_data

def create_pred_df(ticker):
    # LOAD MODELS

    bull_xgb_rcv = pickle.load(open('models/bull_xgb_rcv1.pickle', 'rb'))
    bear_xgb_rcv = pickle.load(open('models/bear_xgb_rcv2.pickle', 'rb'))
    # bull_xgb_rcv = xgb.Booster()
    # bull_xgb_rcv.load_model('models/bull_xgb_rcv1.json')

    # bear_xgb_rcv = xgb.Booster()
    # bear_xgb_rcv.load_model('models/bear_xgb_rcv2.json')
    
    pred_start = pd.datetime.today() - pd.to_timedelta(200, unit='day') 
    pred_end = pd.datetime.today()
    
    bull_columns = ['Returns', 'Unemployment Rate', 'Inflation Rate', 'Misery Index',
       'local_price', 'Bullish', 'Neutral', 'Bearish', 'EMA12_pctchg', 'RSI',
       'Pct_Chg', 'MACD_sentiment', 'Upper_BB_pctchg', 'Lower_BB_pctchg',
       'EMA_sentiment', 'Volume_sentiment']

    bear_columns = ['Bearish', 'Bullish', 'Neutral', 'Returns', 'Inflation Rate',
       'Lower_BB_pctchg', 'Unemployment Rate', 'Upper_BB_pctchg']
    
    # df = web.DataReader(ticker, 'yahoo', pred_start, pred_end)
    df = yfinance.download(ticker, start=pred_start, end=pred_end, threads=True)
    
    adv_stock_indicators(df)

    df['MACD_sentiment'] = list(map(classify_bullish, df['MACD'], df['MACD_Signal']))
    df['EMA_sentiment'] = list(map(classify_bullish, df['EMA26'], df['EMA12']))
    df['Volume_sentiment']  = list(map(classify_bullish, df['Dollar_volume'], df['Rolling_Dollar_volume']))
    
    get_alternative_data()
    alternative_data = pd.read_csv('data/cleaned_alternative_data.csv')
    alternative_data['Date'] = pd.to_datetime(alternative_data['Date'])
    alternative_data.set_index('Date', inplace=True)
    
    full_df = alternative_data.join(df).dropna()
    #Predict buy signals
    full_df['buy_probabilities'] = bull_xgb_rcv.predict_proba(full_df[bull_columns])[:,1]
    full_df['buy_predictions'] = full_df['buy_probabilities'] >= full_df['buy_probabilities'].mean()
    full_df['buy_predictions'] = full_df['buy_predictions'].apply(lambda x: 1 if x == True else 0)

    #Predict sell signals
    full_df['sell_probabilities'] = bear_xgb_rcv.predict_proba(full_df[bear_columns])[:,1]
    full_df['sell_predictions'] = full_df['sell_probabilities'] >= full_df['sell_probabilities'].mean()
    full_df['sell_predictions'] = full_df['sell_predictions'].apply(lambda x: 1 if x == True else 0)
     
    return full_df

def adv_stock_indicators(df):
    df.reset_index()
    #Simple Moving Averages
    df['SMA12'] = df['Close'].rolling(12).mean()
    df['SMA26'] = df['Close'].rolling(26).mean()

    #Exponential Moving Averages
    df['EMA12'] = df['Close'].ewm(span=12).mean()
    df['EMA26'] = df['Close'].ewm(span=26).mean()

    #Using absolute as difference
    df['SMA12_pctchg'] = abs(((df['Close'] - df['SMA12']) / df['SMA12']) * 100) 
    df['SMA26_pctchg'] = abs(((df['Close'] - df['SMA26']) / df['SMA26']) * 100)
    df['EMA12_pctchg'] = abs(((df['Close'] - df['EMA12']) / df['EMA12']) * 100) 
    df['EMA26_pctchg'] = abs(((df['Close'] - df['EMA26']) / df['EMA26']) * 100) 

    #RSI using EMA
    #Default window length: 14
    delta = df['Close'].diff()
    window_length = 14

    up = delta.copy()
    up[delta<=0]=0.0
    down = abs(delta.copy())
    down [delta>0]=0.0

    RS_up = up.ewm(window_length).mean()
    RS_down = down.ewm(window_length).mean()

    rsi= 100-100/(1+RS_up/RS_down)
    df['RSI'] = rsi

    #MACD
    #Default: Fast Length=EMA12, Slow Length=EMA26, MACD Length=EMA9
    df['MACD'] = df['Close'].ewm(span=12).mean() - df['Adj Close'].ewm(span=26).mean()
    df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()

    #Percent Change
    df['Pct_Chg'] = df['Close'].pct_change() * 100
    
    #Bollinger Bands
    df['Upper_BB'] = df['Close'].rolling(window=20).mean() + (df['Close'].rolling(window=20).std() * 2)
    df['Upper_BB_pctchg'] = abs(((df['Close'] - df['Upper_BB']) / df['Upper_BB']) * 100)

    df['Lower_BB'] = df['Close'].rolling(window=20).mean() - (df['Close'].rolling(window=20).std() * 2)
    df['Lower_BB_pctchg'] = abs(((df['Close'] - df['Lower_BB']) / df['Lower_BB']) * 100)
    
    df['Range_BB'] = (df['Upper_BB'] - df['Lower_BB']) / df['Lower_BB'] * 100
    
    #Candlestick Range
    df['Candlestick_range'] = (df['High'] - df['Low']) / df['Low'] * 100
    
    #Dollar Volume
    df['Dollar_volume'] = df['Close'] * df['Volume']
    df['Rolling_Dollar_volume'] = df['Dollar_volume'].rolling(10).mean()

    df.dropna(inplace=True)

def classify_bullish(current, future):
    if float(future) > float(current):
        return 1
    else:
        return 0
    
def classify_bearish(current, future):
    if float(future) < float(current):
        return 1
    else:
        return 0