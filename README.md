## Monk3yStocks App - Predicting Stocks Using Alternative and Technical Data

**UPDATE**: The app is updated and fully deployed on Azure App Services due to Heroku removing their free tier subscription. Note that Azure's free tier subscription has limited compute/day.

### About
This project is a web application using Flask that allows users to view historical stock or crypto prices as candlestick charts with buying/selling trading signals generated from a machine learning model trained on alternative and technical data. This application was containerized using Docker and is currently deployed on Azure App Services.

Try out the web app: https://monk3ystocks.azurewebsites.net/

### Data
#### Alternative Data
- Investor Survey Market Sentiment
- Big Mac Index
- Eurekahedge Hedge Fund Performances
- Misery Index (Unemployment Rate, Inflation Rate, Misery Index)

#### Technical Data
- Exponential Moving Averages
- Relative Strength Indicator
- Moving Average Convergence/Divergence
- Upper and Lower Bollinger Bands
- Volume

### Machine Learning Models
- Logistic Regression
- Naive Bayes Classifier
- Random Forests
- XGBoost

### Library Dependencies
- Flask==2.2.3
- mplfinance==0.12.9b7
- numpy==1.24.2
- pandas==1.5.3
- Quandl==3.7.0
- scikit-learn==1.2.2
- xgboost==1.7.5
- yfinance==0.2.14

### Monk3ystocks App Preview

![monk3ystocks github](https://github.com/rnop/Alternative-and-Technical-Stock-Market-Prediction/blob/master/homepage_png.png "Monk3ystocks Homepage")

![monk3ystocks github](https://github.com/rnop/Alternative-and-Technical-Stock-Market-Prediction/blob/master/SPY_chart.png "SPY Chart and indicators")

### Trading Mantra
* Control Your Emotions - The most difficult thing about trading and investing is handling your emotions when decision-making. The worst thing you could do is enter a position solely based on emotion, for example, jumping into Bitcoin during its moon launch to $20,000 so that you don't get FOMO (Fear Of Missing Out). Being able to stay balanced mentally will allow you to think more rationally and become a better trader.
* Be Prepared to Lose Sometimes - Nobody wins 100% of the time, not even me. I've lost over $1000 in a single trading day, but the worst part wasn't losing the money, it was the negative after-effects it had on my mental health. Once I traded enough, I began to realize that I wasn't going to win all the time and that the best thing I could do after a loss is to prepare myself even better for the next trade.
* Exercise and Eat Healthy - Having a healthy diet and exercising improves how your brain functions allowing you to think more intelligently and rationally. Getting enough sleep is also crucial, especially if you're on the west coast when the market opens at 6:30AM. Just being healthy in general is good for the longevity and happiness of your overall life.
* Take a Break - Trading is like a marathon. You don't want to go all-in on the first lap and risk getting knocked out completely. Pace yourself mentally and physically. Have a hobby that isn't related to the stock market and is mentally challenging (not scrolling through Facebook/Instagram or watching hours of Netflix). For me, it's playing guitar and singing, or exploring the city I am in.
* Do Good Things - Make an effort to help others whenever you can, whether it's donating, volunteering, or simply complimenting somebody. Having a positive mental mindset goes a long way and the attitude you have towards others will translate to the attitude you have around trading. I strive to separate from the stigma of Wall Street that all they care about is themselves and how much money they make.
Family, friends, and health are more important than money.

**DISCLAIMER** Trade at your own risk. This trading app is not guaranteed to make you money. 
