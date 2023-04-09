import quandl
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

def get_alternative_data():
    aaii = quandl.get("AAII/AAII_SENTIMENT", authtoken="xvRAkcY8ExMFtqF9fEK4")
    aaii = aaii[['Bullish','Neutral','Bearish']].pct_change().dropna()
    aaii = aaii[['Bullish','Neutral','Bearish']]
    aaii = aaii.resample('d').ffill().dropna() #forward fill

    #extrapolate last datapoint to today
    aaii_days = ((aaii.tail(1).index  - pd.datetime.today()).days[0]*-1) - 1
    aaii = aaii.append([aaii.tail(1)]*aaii_days)

    aaii_index = pd.date_range('1987/07/31', pd.datetime.today())
    aaii = aaii.set_index(aaii_index)

    bigmac = quandl.get("ECONOMIST/BIGMAC_USA", authtoken="xvRAkcY8ExMFtqF9fEK4")
    bigmac = bigmac['local_price'].pct_change().dropna()
    bigmac = pd.DataFrame(bigmac.resample('d').ffill().dropna())

    #extrapolate last datapoint to today
    bigmac_days = ((bigmac.tail(1).index  - pd.datetime.today()).days[0]*-1) - 1
    bigmac = bigmac.append([bigmac.tail(1)]*bigmac_days)

    bigmac_index = pd.date_range('2001-04-30', pd.datetime.today())
    bigmac = bigmac.set_index(bigmac_index)

    eureka = quandl.get("EUREKA/MEI27", authtoken="xvRAkcY8ExMFtqF9fEK4")
    eureka = eureka['Returns'].pct_change().dropna()
    eureka = pd.DataFrame(eureka.resample('d').ffill().dropna())

    #extrapolate last datapoint to today
    #eureka data updated at weird times so you may have to adjust
    eureka_days = ((eureka.tail(1).index  - pd.datetime.today()).days[0]*-1) - 1
    if eureka_days > 0:
        eureka = eureka.append([eureka.tail(1)]*(eureka_days))
        eureka_index = pd.date_range('2010-09-30', pd.datetime.today())
        eureka = eureka.set_index(eureka_index)

    misery = quandl.get("USMISERY/INDEX", authtoken="xvRAkcY8ExMFtqF9fEK4")
    misery = misery[['Unemployment Rate','Inflation Rate','Misery Index']].pct_change().dropna()
    misery = misery[['Unemployment Rate','Inflation Rate','Misery Index']]
    misery = misery.resample('d').ffill().dropna()

    #extrapolate last datapoint to today
    misery_days = ((misery.tail(1).index  - pd.datetime.today()).days[0]*-1) - 1
    misery = misery.append([misery.tail(1)]*misery_days)

    misery_index = pd.date_range('1948-02-29', pd.datetime.today())
    misery = misery.set_index(misery_index)

    #alternative_data = eureka.join(misery).join(bigmac).join(aaii).join(reddit)
    alternative_data = eureka.join(misery).join(bigmac).join(aaii)
    alternative_data.replace([np.inf, -np.inf], np.nan, inplace=True)
    alternative_data.dropna(inplace=True)

    return alternative_data

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

    df['MACD_sentiment'] = list(map(classify_bullish, df['MACD'], df['MACD_Signal']))
    df['EMA_sentiment'] = list(map(classify_bullish, df['EMA26'], df['EMA12']))
    df['Volume_sentiment']  = list(map(classify_bullish, df['Dollar_volume'], df['Rolling_Dollar_volume']))

    df.dropna(inplace=True) 
    

    return df

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
    
def get_full_technical_data(ticker):
    technical_data = yf.download(ticker, period='120d')

    today_data = {'Open': yf.Ticker(ticker).info['regularMarketOpen'],
                'High': yf.Ticker(ticker).info['regularMarketDayHigh'],
                'Low': yf.Ticker(ticker).info['regularMarketDayLow'],
                'Close': yf.Ticker(ticker).info['regularMarketPrice'],
                'Adj Close': yf.Ticker(ticker).info['regularMarketPrice'],
                'Volume': yf.Ticker(ticker).info['regularMarketVolume'],
                'Date': datetime.today().strftime('%Y-%m-%d')}
                
    today_df = pd.DataFrame([today_data])

    # set the datetime column as the index
    today_df.set_index('Date', inplace=True)
    today_df.index = pd.to_datetime(today_df.index)
    full_technical_data = pd.concat([technical_data, today_df])
    full_technical_data = adv_stock_indicators(full_technical_data)

    return full_technical_data

def get_model_predictions(full_df, bull_model, bear_model, features):
    full_df['buy_signal_proba'] = bull_model.predict_proba(full_df[features])[:,1]
    full_df['buy_signal'] = full_df['buy_signal_proba'] >= 0.8
    full_df['buy_marker'] = full_df.apply(lambda x: x['Low'] - (x['Low'] * 0.01) if x['buy_signal'] else None, axis=1)

    full_df['sell_signal_proba'] = bear_model.predict_proba(full_df[features])[:,1]
    full_df['sell_signal'] = full_df['sell_signal_proba'] >= 0.30
    full_df['sell_marker'] = full_df.apply(lambda x: x['High'] + (x['High'] * 0.01) if x['sell_signal'] else None, axis=1)
    return full_df