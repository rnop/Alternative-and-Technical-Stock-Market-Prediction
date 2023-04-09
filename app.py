from flask import Flask, render_template, request
import yfinance as yf
import mplfinance as mpf
import pandas as pd
import numpy as np
import base64
import utils
import pickle

# Function to plot the chart in a separate thread
app = Flask(__name__, template_folder='templates')

@app.route('/', methods=['GET', 'POST'])
def index():
    # Default Stock Ticker
    ticker = "SPY"
    if request.method == 'POST':
        # Retrieve the ticker symbol entered by the user
        ticker = request.form['ticker']

    try:
        technical_data = utils.get_full_technical_data(ticker)
    except:
        # If there's an error downloading the data, use the default ticker instead
        ticker = "SPY"
        technical_data = utils.get_full_technical_data(ticker)

    # Scrape Alternative + Technical Data
    alternative_data = utils.get_alternative_data()
    
    full_df = alternative_data.join(technical_data)
    full_df.replace([np.inf, -np.inf], np.nan, inplace=True)
    full_df.dropna(inplace=True)

    # Get Model Predictions
    with open('bull_xgb_model.pkl', 'rb') as f:
        bull_model = pickle.load(f)

    # Load the model from a file
    with open('bear_xgb_model.pkl', 'rb') as f:
        bear_model = pickle.load(f)

    features = ['Returns', 'Unemployment Rate', 'Inflation Rate', 'Misery Index',
        'local_price', 'Bullish', 'Neutral', 'Bearish', 'EMA12_pctchg', 'RSI',
        'Pct_Chg', 'MACD_sentiment', 'Upper_BB_pctchg', 'Lower_BB_pctchg',
        'EMA_sentiment', 'Volume_sentiment']

    full_df = utils.get_model_predictions(full_df, bull_model, bear_model, features)

    
    # get today's prediction
    today = full_df.tail(1)
    if today['buy_signal'][0] == today['sell_signal'][0]:
        ten_day_prediction = 'Neutral'
    elif today['buy_signal'][0] == True:
        ten_day_prediction = 'Bullish'
    elif today['sell_signal'][0] == True:
        ten_day_prediction = 'Bearish'

    # Visualize last 90 trading days
    n_obs = 90
    plot_data = full_df.tail(n_obs)
    start_date = plot_data.index[0].strftime('%Y-%m-%d')
    todays_date = plot_data.index[-1].strftime('%Y-%m-%d')
    mc = mpf.make_marketcolors(up='g',down='r',
                            edge='black',
                            wick={'up':'black','down':'black'},
                            volume='in',
                            ohlc='black')
    s  = mpf.make_mpf_style(marketcolors=mc, gridstyle='--')

    mpf.plot(plot_data, type='candle', volume=True, 
            title=f"\n\n\n {ticker} Historical Stock Price + Machine Learning Predictions \n Dates: {start_date} - {todays_date} \n Current 10-Day Prediction: {ten_day_prediction}",
            ylabel='Price ($)', mav=(7, 14), figratio=(15, 8), figscale=1.4,
            style='nightclouds', show_nontrading=False, 
            addplot=[
                mpf.make_addplot(plot_data['buy_marker'], type='scatter', markersize=24, marker='^', color='green', panel=0, ylabel='Buy Signals'),
                mpf.make_addplot(plot_data['sell_marker'], type='scatter', markersize=24, marker='v', color='red', panel=0, ylabel='Sell Signals'),
            ], savefig='chart.png')
    
    # Store the chart data in the queue
    with open('chart.png', 'rb') as f:
        chart_data = base64.b64encode(f.read()).decode('utf-8')

    # Render template with candlestick chart and form
    return render_template('index.html', chart_data=chart_data, ticker=ticker)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80)