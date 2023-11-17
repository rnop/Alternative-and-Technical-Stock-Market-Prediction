from flask import Flask, render_template, request
import yfinance as yf
from datetime import datetime, timedelta
import pandas_ta as ta
import pandas as pd
import numpy as np

import plotly
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json

from joblib import load


app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    graphJSON = None
    ticker = 'SPY'  # Default ticker

    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    if request.method == 'POST':
        user_input = request.form['ticker']
        
        # Attempt to fetch data for the user-provided ticker
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

        
        df_sorted = df.sort_index().tail(90)

        # Get starting and end dates
        df_start = df_sorted.index[0].strftime('%Y-%m-%d')
        df_end = df_sorted.index[-1].strftime('%Y-%m-%d')

        # Plotly chart code
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.03, 
                        row_heights=[0.6, 0.2, 0.2],  # Adjust these values as needed
                        subplot_titles=(f"{df_start} to {df_end}", '', ''))
    
        fig.update_layout(width=1400, height=800)

        candlestick = go.Candlestick(x=df_sorted.index, 
                                    open=df_sorted['Open'], 
                                    high=df_sorted['High'], 
                                    low=df_sorted['Low'], 
                                    close=df_sorted['Close'],
                                    increasing_line_color='green', 
                                    decreasing_line_color='red')
        
        fig.add_trace(candlestick, row=1, col=1)

        # Add trading signals
        # Generate "random" machine learning model predictions
        bull_model = load('bull_rf_model_threshold81.joblib')
        bear_model = load('bear_rf_model_threshold52.joblib')

        train_features = ['SMA50_PCTCHG','SMA200_PCTCHG', 'SMA_BULLISH','EMA12_PCTCHG', 'EMA26_PCTCHG', 'EMA_BULLISH', 'LOWERBBAND_PCTCHG', 'MIDBBAND_PCTCHG', 'UPPERBBAND_PCTCHG', 'RSI']
        # bull predictions
        prob_predictions = bull_model.predict_proba(df[train_features])
        prob_class_1 = prob_predictions[:, 1]
        threshold = 0.7
        threshold_predictions = np.where(prob_class_1 > threshold, 1, 0)
        df['BUY_PREDICTION'] = threshold_predictions

        # bear predictions
        prob_predictions = bear_model.predict_proba(df[train_features])
        prob_class_1 = prob_predictions[:, 1]
        threshold = 0.52
        threshold_predictions = np.where(prob_class_1 > threshold, 1, 0)
        df['SELL_PREDICTION'] = threshold_predictions

        # Sort df
        df_sorted = df.sort_index().tail(90)

        # Add trading signals
        buy_signals = df_sorted[df_sorted['BUY_PREDICTION'] == 1]
        sell_signals = df_sorted[df_sorted['SELL_PREDICTION'] == 1]

        # Calculate offset for Buy and Sell signals
        offset_pct = 0.024
        buy_signal_offset = buy_signals['Low'] * (1 - offset_pct)
        sell_signal_offset = sell_signals['High'] * (1 + offset_pct)

        # Add Buy signals (Green dots below the Low price with offset)
        fig.add_trace(go.Scatter(
            x=buy_signals.index, 
            y=buy_signal_offset, 
            mode='markers', 
            marker=dict(color='darkgreen', size=10, symbol='star-triangle-up'),
            name='14D-BUYSIGNAL' # BUY SIGNAL LABEL
        ), row=1, col=1)

        # Add Sell signals (Red dots above the High price with offset)
        fig.add_trace(go.Scatter(
            x=sell_signals.index, 
            y=sell_signal_offset, 
            mode='markers', 
            marker=dict(color='maroon', size=10, symbol='star-triangle-down'),
            name='14D-SELLSIGNAL' # SELL SIGNAL LABEL
        ), row=1, col=1)

        # Custom colors for EMAs
        fig.add_trace(go.Scatter(x=df_sorted.index, y=df_sorted['EMA_12'], mode='lines', name='EMA 12', line=dict(width=0.7, color='purple')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_sorted.index, y=df_sorted['EMA_26'], mode='lines', name='EMA 26', line=dict(width=0.7, color='blue')), row=1, col=1)

        # Custom colors for Bollinger Bands
        fig.add_trace(go.Scatter(x=df_sorted.index, y=df_sorted['BBL_20_2.0'], mode='lines', name='Lower BBand', line=dict(width=0.7, color='orange')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_sorted.index, y=df_sorted['BBU_20_2.0'], mode='lines', name='Higher BBand', line=dict(width=0.7, color='orange')), row=1, col=1)

        # Custom color for Volume bar chart
        fig.add_trace(go.Bar(x=df_sorted.index, y=df_sorted['Volume'], name='Volume', marker_color='purple'), row=2, col=1)

        # Custom color for RSI line chart
        fig.add_trace(go.Scatter(x=df_sorted.index, y=df_sorted['RSI'], mode='lines', name='RSI', line=dict(width=1, color='black')), row=3, col=1)

        # Change colors for RSI overbought and oversold lines
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)


        fig.update_layout(
            width=1400, 
            height=800,
            title={
                'text': f'{ticker} (14-Day BUY/SELL Signals)',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            xaxis_rangeslider_visible=False, 
            showlegend=False,
            yaxis2_title="Volume",  # Set y-axis title for Volume subplot
            yaxis3_title="RSI"     # Set y-axis title for RSI subplot
        )   
        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('index.html', graphJSON=graphJSON, ticker=ticker)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False)
