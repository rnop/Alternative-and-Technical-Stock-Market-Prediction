import yfinance as yf
from datetime import datetime, timedelta
import pandas_ta as ta

import json
import pandas as pd
import numpy as np
from datetime import datetime
from joblib import load

def get_stock_data(user_input, start_date):
    df = yf.download(user_input, start=start_date.strftime('%Y-%m-%d'))
            
    # Check if the data is valid, if not, use the default ticker
    if df.empty:
        df = yf.download(ticker, start=start_date.strftime('%Y-%m-%d'))
    else:
        ticker = user_input  # Update ticker to user input if valid

    df['SMA_50'] = ta.sma(df['Close'], length=50)
    df['SMA_200'] = ta.sma(df['Close'], length=200)

    df['EMA_12'] = ta.ema(df['Close'], length=12)
    df['EMA_26'] = ta.ema(df['Close'], length=26)

    df['RSI'] = ta.rsi(df['Close'], length=14)

    macd = ta.macd(df['Close'], fast=12, slow=26, signal=9)
    df = df.join(macd)

    bollinger = ta.bbands(df['Close'], length=20, std=2)
    df = df.join(bollinger)
    df.dropna(inplace=True)

    # Train features
    df['SMA50_PCTCHG'] = ((df['SMA_50'] - df['Close']) / df['Close']) * 100
    df['SMA200_PCTCHG'] = ((df['SMA_200'] - df['Close']) / df['Close']) * 100
    df['SMA_BULLISH'] = (df['SMA_50'] > df['SMA_200']).astype(int)

    df['EMA12_PCTCHG'] = ((df['EMA_12'] - df['Close']) / df['Close']) * 100
    df['EMA26_PCTCHG'] = ((df['EMA_26'] - df['Close']) / df['Close']) * 100
    df['EMA_BULLISH'] = (df['EMA_12'] > df['EMA_26']).astype(int)

    df['LOWERBBAND_PCTCHG'] = ((df['BBL_20_2.0'] - df['Close']) / df['Close']) * 100
    df['MIDBBAND_PCTCHG'] = ((df['BBM_20_2.0'] - df['Close']) / df['Close']) * 100
    df['UPPERBBAND_PCTCHG'] = ((df['BBU_20_2.0'] - df['Close']) / df['Close']) * 100

    return df

def generate_bull_signal(df):
    # load bull model
    bull_model = load('models/bull_rf_model_threshold81.joblib')
    train_features = ['SMA50_PCTCHG','SMA200_PCTCHG', 'SMA_BULLISH','EMA12_PCTCHG', 'EMA26_PCTCHG', 'EMA_BULLISH', 'LOWERBBAND_PCTCHG', 'MIDBBAND_PCTCHG', 'UPPERBBAND_PCTCHG', 'RSI']
    # bull predictions
    prob_predictions = bull_model.predict_proba(df[train_features])
    prob_class_1 = prob_predictions[:, 1]
    threshold = 0.7
    threshold_predictions = np.where(prob_class_1 > threshold, 1, 0)
    return threshold_predictions

def generate_bear_signal(df):
    # load bear model
    bear_model = load('models/bear_rf_model_threshold52.joblib')
    train_features = ['SMA50_PCTCHG','SMA200_PCTCHG', 'SMA_BULLISH','EMA12_PCTCHG', 'EMA26_PCTCHG', 'EMA_BULLISH', 'LOWERBBAND_PCTCHG', 'MIDBBAND_PCTCHG', 'UPPERBBAND_PCTCHG', 'RSI']
    # bear predictions
    prob_predictions = bear_model.predict_proba(df[train_features])
    prob_class_1 = prob_predictions[:, 1]
    threshold = 0.52
    threshold_predictions = np.where(prob_class_1 > threshold, 1, 0)
    return threshold_predictions

