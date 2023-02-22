from flask import Flask, render_template, request

import yfinance
# import simplejson
import requests

import pandas as pd
# import pandas_datareader as web
from utils import get_alternative_data, adv_stock_indicators, create_pred_df

from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import DatetimeTickFormatter, Title, Legend

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/graph', methods=['POST'])

def graph():
    app.vars = {}
    app.vars['ticker'] = request.form['ticker']
    
    if app.vars['ticker'] == '':
        predict_ticker = 'SPY'
    else:
        predict_ticker = app.vars['ticker']
    
    df = create_pred_df(predict_ticker)
    print(df.head())
    df1 = df

    inc = df1['Close'] > df1['Open']
    dec = df1['Open'] > df1['Close']
    w = 12*60*60*1000

    p = figure(title= f'{predict_ticker}'+ ' Chart\n', 
               sizing_mode = 'stretch_width', 
               # height=500,  
               y_axis_label='Price (USD)',
               y_range=(min(df1['Close'])/1.20, max(df1['High'])*1.10))

    #background
    p.background_fill_color = "white"
    p.background_fill_alpha = 0.5

    #gridlines
    p.xgrid.minor_grid_line_color = 'navy'
    p.xgrid.minor_grid_line_alpha = 0.05
    p.ygrid.minor_grid_line_color = 'navy'
    p.ygrid.minor_grid_line_alpha = 0.05

    #title
    p.title.text_font_size = '30pt'
    p.title.align = 'center'
    
    if df1.tail(1)['buy_predictions'].values[0] == True:
        p.add_layout(Title(
            text= "10-Day Predictions for "+ f"{df1.tail(1).index[0].strftime('%m/%d/%Y')}: " + "BUY" 
            , text_font_size="16pt"), 'above') 
    elif df1.tail(1)['sell_predictions'].values[0] == True:
        p.add_layout(Title(
            text= "10-Day Predictions for "+ f"{df1.tail(1).index[0].strftime('%m/%d/%Y')}: " + "SELL" 
            , text_font_size="16pt"), 'above')
    else:
        p.add_layout(Title(
            text= "10-Day Predictions for "+ f"{df1.tail(1).index[0].strftime('%m/%d/%Y')}: " + "UNCERTAIN" 
            , text_font_size="16pt"), 'above')

    #axes
    p.xaxis.axis_label_text_font_size = "13pt"
    p.yaxis.axis_label_text_font_size = "13pt"
    p.xaxis.formatter=DatetimeTickFormatter(days="%m/%d")
    p.xaxis.ticker.desired_num_ticks=30
    p.xaxis.major_label_orientation = "vertical"

    #Candlestick
    p.segment(df1.index, df1['High'], df1.index, df1['Low'], color='black')
    p.vbar(df1.index[inc], w, df1['Open'][inc], df1['Close'][inc], fill_color='green', line_color='black')
    p.vbar(df1.index[dec], w, df1['Open'][dec], df1['Close'][dec], fill_color='red', line_color='black')

    #EMA
    e12 = p.line(df1.index, df1['EMA12'], line_color='darkorange', line_dash='dotted', alpha=0.90)
    e26 = p.line(df1.index, df1['EMA26'], line_color='navy', line_dash='dotted', alpha=0.90)

    #BBs
    bb = p.line(df1.index, df1['Upper_BB'], line_color='black', line_dash='solid', alpha=0.50)
    p.line(df1.index, df1['Lower_BB'], line_color='black', line_dash='solid', alpha=0.50)

    #ML Prediction
    buy_ml = p.circle(df1.index, (df1['Low']*df1['buy_predictions']) - (df1['Low'] * 0.05), size=7, color='darkgreen', fill_alpha=0.50)
    sell_ml = p.circle(df1.index, (df1['High']*df1['sell_predictions']) + (df1['High'] * 0.05), size=7, color='darkred', fill_alpha=0.50)
    
    #Volume
    bar = figure(
                sizing_mode = 'stretch_width', height=100,
                y_axis_label='Volume')
    
    bar.yaxis.axis_label_text_font_size = "13pt"
    bar.xaxis.formatter=DatetimeTickFormatter()
    bar.xaxis.ticker.desired_num_ticks=10
    bar.vbar(df1.index, top = df1['Volume']/1000000, width=10)

    #RSI 
    p2 = figure(
                sizing_mode = 'stretch_width', height=125,
                x_axis_label='Date',
                y_axis_label='RSI')
    p2.yaxis.axis_label_text_font_size = "13pt"
    p2.xaxis.axis_label_text_font_size = "13pt"

    p2.xaxis.formatter=DatetimeTickFormatter()
    p2.xaxis.ticker.desired_num_ticks=10
    p2.line(df1.index, df1['RSI'], line_color='orange')
    p2.line(df1.index, 70, line_color='gray', line_dash='dashed')
    p2.line(df1.index, 30, line_color='gray', line_dash='dashed')

    script, div = components(p)
    script2, div2 = components(p2)
    scriptbar, divbar = components(bar)
    
    if request.form.get('All'):
        e12 = p.line(df.index, df['EMA12'], line_color='darkorange', line_dash='dotted', alpha=0.90)
        e26 = p.line(df.index, df['EMA26'], line_color='navy', line_dash='dotted', alpha=0.90)
        bb = p.line(df.index, df['Upper_BB'], line_color='black', line_dash='solid', alpha=0.50)
        p.line(df.index, df['Lower_BB'], line_color='black', line_dash='solid', alpha=0.50)
        script, div = components(p)
        return render_template('graph.html', script=script, div=div, script2=script2, div2=div2 , scriptbar=scriptbar, divbar=divbar)
    
    if request.form.get('RSI') and not request.form.get('Volume'):
        return render_template('graph.html', script=script, div=div, script2=script2, div2=div2)
    
    if request.form.get('Volume') and not request.form.get('RSI'):
        return render_template('graph.html', script=script, div=div, scriptbar=scriptbar, divbar=divbar)
    
    if not request.form.get('RSI') and not request.form.get('Volume'):
        return render_template('graph.html', script=script, div=div)
    
    if request.form.get('RSI') and request.form.get('Volume'):
        return render_template('graph.html', script=script, div=div, script2=script2, div2=div2 , scriptbar=scriptbar, divbar=divbar)
       
if __name__ == '__main__':
  app.run(port=33507)