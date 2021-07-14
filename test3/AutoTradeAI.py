import time
import pyupbit
import datetime
import schedule
from fbprophet import Prophet
import requests

access = ""
secret = ""

def post_message(token, channel, text):
    """슬랙 메시지 전송"""
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+token},
        data={"channel": channel,"text": text}
    )

myToken = ""

def dbgout(message):
    """인자로 받은 문자열을 파이썬 셸과 슬랙으로 동시에 출력한다."""
    print(datetime.datetime.now().strftime('[%m/%d %H:%M:%S]'), message)
    strbuf = datetime.datetime.now().strftime('[%m/%d %H:%M:%S] ') + message
    post_message(myToken,"#stock", strbuf)

def report(ticker):
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    percent =(df.iloc[0]['high'] - df.iloc[0]['low']) * 0.5
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    target_price = df.iloc[0]['low'] + percent
    btc_current_price = get_current_price(ticker)
    dbgout('현재 가격: ' + str(round(btc_current_price)))
    dbgout('당일 저가: ' + str(round(df.iloc[0]['low'])))
    dbgout('매수 목표 가격: ' + str(round(target_price)))
    dbgout('매도 목표 시간: ' + '오전' + str(pricemax) + '시')
    dbgout('매도 예측 가격: ' + str(predicted_close_price))

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    percent =(df.iloc[0]['high'] - df.iloc[0]['low']) * k
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    target_price = df.iloc[0]['low'] + percent
    return target_price

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def get_balance(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]

predicted_close_price = 0
def predict_price(ticker):
    """Prophet으로 당일 종가 가격 예측"""
    global predicted_close_price
    global pricemax
    global pricemin
    three_days = []
    week = []
    month = []
    one_hundred_days = []

    df = pyupbit.get_ohlcv(ticker, count=72, interval="minute60")
    df = df.reset_index()
    df['ds'] = df['index']
    df['y'] = df['close']
    data = df[['ds','y']]
    model = Prophet()
    model.fit(data)
    future = model.make_future_dataframe(periods=24, freq='H')
    forecast = model.predict(future)
    for i in range(clock,10):
        closeDf = forecast[forecast['ds'] == forecast.iloc[-1]['ds'].replace(hour=i)]
        if len(closeDf) == 0:
            closeDf = forecast[forecast['ds'] == data.iloc[-1]['ds'].replace(hour=i)]
        closeValue = closeDf['yhat'].values[0]
        three_days.append(closeValue)

    df = pyupbit.get_ohlcv(ticker, count=168, interval="minute60")
    df = df.reset_index()
    df['ds'] = df['index']
    df['y'] = df['close']
    data = df[['ds','y']]
    model = Prophet()
    model.fit(data)
    future = model.make_future_dataframe(periods=24, freq='H')
    forecast = model.predict(future)
    for i in range(clock,10):
        closeDf = forecast[forecast['ds'] == forecast.iloc[-1]['ds'].replace(hour=i)]
        if len(closeDf) == 0:
            closeDf = forecast[forecast['ds'] == data.iloc[-1]['ds'].replace(hour=i)]
        closeValue = closeDf['yhat'].values[0]
        week.append(closeValue)

    df = pyupbit.get_ohlcv(ticker, count=744, interval="minute60")
    df = df.reset_index()
    df['ds'] = df['index']
    df['y'] = df['close']
    data = df[['ds','y']]
    model = Prophet()
    model.fit(data)
    future = model.make_future_dataframe(periods=24, freq='H')
    forecast = model.predict(future)
    for i in range(clock,10):
        closeDf = forecast[forecast['ds'] == forecast.iloc[-1]['ds'].replace(hour=i)]
        if len(closeDf) == 0:
            closeDf = forecast[forecast['ds'] == data.iloc[-1]['ds'].replace(hour=i)]
        closeValue = closeDf['yhat'].values[0]
        month.append(closeValue)

    df = pyupbit.get_ohlcv(ticker, count=2400, interval="minute60")
    df = df.reset_index()
    df['ds'] = df['index']
    df['y'] = df['close']
    data = df[['ds','y']]
    model = Prophet()
    model.fit(data)
    future = model.make_future_dataframe(periods=24, freq='H')
    forecast = model.predict(future)
    for i in range(clock,10):
        closeDf = forecast[forecast['ds'] == forecast.iloc[-1]['ds'].replace(hour=i)]
        if len(closeDf) == 0:
            closeDf = forecast[forecast['ds'] == data.iloc[-1]['ds'].replace(hour=i)]
        closeValue = closeDf['yhat'].values[0]
        one_hundred_days.append(closeValue)
    
    c = [(three_days[i]+week[i]+month[i]+one_hundred_days[i])/4 for i in range(len(week))]
    pricemax = c.index(max(c))
    pricemin = c.index(min(c))
    
    predicted_close_price = round(max(c))

clock = 0
def time_cnt_a():
    now = datetime.datetime.now()
    start_time = get_start_time("KRW-BTC")
    global clock
    if start_time < now < start_time + datetime.timedelta(hours = 15):
        clock = 0
    elif start_time + datetime.timedelta(hours = 15) < now < start_time + datetime.timedelta(hours = 16):
        clock = 1
    elif start_time + datetime.timedelta(hours = 16) < now < start_time + datetime.timedelta(hours = 17):
        clock = 2
    elif start_time + datetime.timedelta(hours = 17) < now < start_time + datetime.timedelta(hours = 18):
        clock = 3
    elif start_time + datetime.timedelta(hours = 18) < now < start_time + datetime.timedelta(hours = 19):
        clock = 4
    elif start_time + datetime.timedelta(hours = 19) < now < start_time + datetime.timedelta(hours = 20):
        clock = 5
    elif start_time + datetime.timedelta(hours = 20) < now < start_time + datetime.timedelta(hours = 21):
        clock = 6
    elif start_time + datetime.timedelta(hours = 21) < now < start_time + datetime.timedelta(hours = 22):
        clock = 7
    elif start_time + datetime.timedelta(hours = 22) < now < start_time + datetime.timedelta(hours = 23):
        clock = 8
    elif start_time + datetime.timedelta(hours = 23) < now < start_time + datetime.timedelta(hours = 24):
        clock = 9

time_cnt_a()
predict_price("KRW-BTC")
report("KRW-BTC")
schedule.every().hour.do(lambda: predict_price("KRW-BTC"))
schedule.every().hour.do(lambda: report("KRW-BTC"))

# 로그인
upbit = pyupbit.Upbit(access, secret)
dbgout("autotrade start")
cnt = 0

# 자동매매 시작
while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time("KRW-BTC")
        end_time = start_time + datetime.timedelta(days=1)
        sell_time = start_time + datetime.timedelta(hours=pricemax+15+clock)
        schedule.run_pending()
        btc = get_balance("BTC")

        if start_time + datetime.timedelta(seconds=30) < now < sell_time - datetime.timedelta(seconds=10):
            target_price = get_target_price("KRW-BTC", 0.5)
            current_price = get_current_price("KRW-BTC")
            krw = get_balance("KRW")
            if krw > 5000 and cnt == 0:
                if target_price < current_price and current_price < predicted_close_price:
                    upbit.buy_market_order("KRW-BTC", krw*0.9995)
                    dbgout("BTC buy : " +str(current_price))
                    time.sleep(600)

            elif target_price > current_price and krw*3 < btc*current_price + krw:
                if btc > 0.00008:
                    upbit.sell_market_order("KRW-BTC", btc*0.5)
                    dbgout("BTC sell half: " +str(current_price))

        elif start_time < now < start_time + datetime.timedelta(seconds=30):
            cnt = 0

        else:
            if btc > 0.00008:
                current_price = get_current_price("KRW-BTC")
                upbit.sell_market_order("KRW-BTC", btc)
                cnt = 1
                dbgout("BTC sell : " +str(current_price))

        time.sleep(1)
    except Exception as e:
        print(e)
        time.sleep(1)
