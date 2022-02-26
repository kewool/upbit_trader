from re import I
from ta.trend import SMAIndicator, WMAIndicator, EMAIndicator, MACD
from ta.momentum import RSIIndicator, StochRSIIndicator
from ta.volatility import BollingerBands
from ta.volume import VolumeWeightedAveragePrice
import pyupbit
import time
import datetime
import requests
import sys
import pandas as pd
import numpy as np

def get_sma(close, period):
    df_sma = SMAIndicator(close, window=period).sma_indicator()
    return df_sma

def add_sma(df, close, *sma):
    for i in sma:
        df[f"sma{i}"] = get_sma(close, i)
    return df

def get_wma(close, period):
    df_wma = WMAIndicator(close, window=period).wma()
    return df_wma

def add_wma(df, close, *wma):
    for i in wma:
        df[f"wma{i}"] = get_wma(close, i)
    return df

def get_ema(close, period):
    df_ema = EMAIndicator(close, window=period).ema_indicator()
    return df_ema

def add_ema(df, close, *ema):
    for i in ema:
        df[f"ema{i}"] = get_ema(close, i)
    return df

def get_macd(close, period_slow, period_fast, period_sign):
    macd = MACD(close, window_slow=period_slow, window_fast=period_fast, window_sign=period_sign)
    df_macd = macd.macd()
    df_macd_s = macd.macd_signal()
    df_macd_d = macd.macd_diff()
    return df_macd, df_macd_s, df_macd_d

def add_macd(df, close, period_slow, period_fast, period_sign):
    macd = get_macd(close, period_slow, period_fast, period_sign)
    df['macd'] = macd[0]
    df['macd_s'] = macd[1]
    df['macd_d'] = macd[2]
    return df

def get_rsi(close, period):
    df_rsi = RSIIndicator(close, window=period).rsi()
    return df_rsi

def add_rsi(df, close, *rsi):
    for i in rsi:
        df[f"rsi{i}"] = get_rsi(close, i)
    return df

def get_stochrsi(close, period, period_smooth1, period_smooth2):
    stochrsi = StochRSIIndicator(close, window=period, smooth1=period_smooth1, smooth2=period_smooth2)
    df_srsi = stochrsi.stochrsi()
    df_srsik = stochrsi.stochrsi_k()
    df_srsid = stochrsi.stochrsi_d()
    return df_srsi, df_srsik, df_srsid

def add_stochrsi(df, close, period, period_smooth1, period_smooth2):
    stochrsi = get_stochrsi(close, period, period_smooth1, period_smooth2)
    df["srsi"] = stochrsi[0]
    df["srsik"] = stochrsi[1]
    df["srsid"] = stochrsi[2]
    return df

def get_bb(close, period, period_dev):
    bb = BollingerBands(close, window=period, window_dev=period_dev)
    df_bh = bb.bollinger_hband()
    df_bhi = bb.bollinger_hband_indicator()
    df_bl = bb.bollinger_lband()
    df_bli = bb.bollinger_lband_indicator()
    df_bm = bb.bollinger_mavg()
    df_bw = bb.bollinger_wband()
    return df_bh, df_bhi, df_bl, df_bli, df_bm, df_bw

def add_bb(df, close, period, period_dev):
    bb = get_bb(close, period, period_dev)
    df["bh"] = bb[0]
    df["bhi"] = bb[1]
    df["bl"] = bb[2]
    df["bli"] = bb[3]
    df["bm"] = bb[4]
    df["bw"] = bb[5]
    return df

def get_vwap(high, low, close, volume, period):
    vwap = VolumeWeightedAveragePrice(high=high, low=low, close=close, volume=volume, window=period)
    df_vwap = vwap.volume_weighted_average_price()
    return df_vwap

def add_vwap(df, high, low, close, volume, period):
    df["vwap"] = get_vwap(high, low, close, volume, period)
    return df

def get_buy_amount(buy_amt_unit, buy_cnt_limit, increase_rate):
    buy_amt = 0
    buy_amt_list = [0.0]
    for i in range(buy_cnt_limit):
        amt = buy_amt_unit + buy_amt * increase_rate
        buy_amt = round(buy_amt + amt, 4)
        buy_amt_list.append(buy_amt)
    return buy_amt_list

def get_max_loss(close, buy_amt_unit, buy_cnt_limit, increase_rate, max_loss_rate):
    buy_amt = 0
    buy_price = 0
    for i in range(buy_cnt_limit):
        amt = buy_amt_unit + buy_amt * increase_rate
        buy_price = round(buy_price + close * amt, 4)
        buy_amt = round(buy_amt + amt, 4)
    return round(buy_price * max_loss_rate, 4)

def adj_revenue(revenue, close, buy_amt_unit, buy_cnt_limit, increase_rate):
    open_amt_list = get_buy_amount(buy_amt_unit, buy_cnt_limit, increase_rate)
    max_amt = open_amt_list[len(open_amt_list)-1]
    adj_revenue = (30 * revenue) / max_amt
    return adj_revenue

def run_test(df, config):
    revenue_rate = config["revenue_rate"]
    max_loss_rate = config["max_loss_rate"]
    increase_rate = config["increase_rate"]
    buy_cnt_limit = int(config["buy_cnt_limit"])
    buy_amt_unit = config["buy_amt_unit"]

    trade_fee = 0.001
    close = 880

    buy_amt_list = get_buy_amount(buy_amt_unit, buy_cnt_limit, increase_rate)
    max_loss = get_max_loss(close, buy_amt_unit, buy_cnt_limit, increase_rate, max_loss_rate)

    buy_cnt = 0
    buy_price = 0
    buy_amt = 0
    revenue = 0
    revenue_t = 0
    buy_cnt_tot = 0

    df = df.iloc[df.shape[0]-144000:df.shape[0]-124000]
    for i in range(df.shape[0]-1):
        close1 = round(df.iloc[i:i+1]['c'].values[0], 4)
        close2 = round(df.iloc[i+1:i+2]['c'].values[0], 4)
        wma7 = round(df.iloc[i:i+1]["wma7"].values[0], 4)
        wma99 = round(df.iloc[i:i+1]["wma99"].values[0], 4)
        vwap = round(df.iloc[i:i+1]["vwap"].values[0], 4)

        loss = buy_price - close2 * buy_amt
        if loss > max_loss:
            revenue_t = close2 * buy_amt - buy_price - buy_price * trade_fee
            revenue = round(revenue + revenue_t, 4)
            buy_cnt = 0
            buy_amt = 0
            buy_price = 0
            continue

        tp_revenue = close2 * buy_amt - (buy_price + buy_price * revenue_rate)
        if buy_cnt > 0 and tp_revenue > 0:
            revenue_t = close2 * buy_amt - buy_price - buy_price * trade_fee
            revenue = round(revenue + revenue_t, 4)
            buy_cnt = 0
            buy_amt = 0
            buy_price = 0
            continue

        if buy_cnt < buy_cnt_limit and close2 < vwap and close2 < wma7 and wma7 > wma99:
            t_amt = buy_amt_unit + buy_amt * increase_rate
            buy_price = round(buy_price + close2 * t_amt, 4)
            buy_amt = round(buy_amt + t_amt, 4)
            buy_cnt += 1
            buy_cnt_tot += 1
    return adj_revenue(revenue, close, buy_amt_unit, buy_cnt_limit, increase_rate)
    
def get_current_price(coin):
    message = ""
    result = "none"
    try:
        result = pyupbit.get_current_price(coin)
    except:
        message = f"{sys.exc_info()}"
    
    try:
        message = result["error"]["message"]
    except:
        if message == "":
            message = "good"
    return message, result

def get_balance(api, coin):
    message = ""
    result = "none"
    trade_coin = "none"
    buy_amt = 0
    buy_price = 0
    try:
        trade_coin = coin.split('-')[1]
        result = api.get_balances()
    except:
        message = f"{sys.exc_info()}"
    
    try:
        message = result[0]["error"]["message"]
    except:
        if message == "":
            message = "good"
    
    if message == "good":
        for i in result:
            if i["currency"] == trade_coin:
                buy_amt = i["balance"]
                buy_price = i["avg_buy_price"]
    return message, buy_amt, buy_price

def get_order_status(api, uuid):
    message = ""
    state = "none"
    price = "none"
    amt = "none"
    result = {"state":"none", "side":"none", "price":"0", "volume":"0"}

    try:
        result = api.get_order(uuid)
    except:
        message = f"{sys.exc_info()}"

    try:
        message = result["error"]["message"]
    except:
        if message == "":
            message = "good"
            state = result["state"]
            price = result["price"]
            amt = result["volume"]
    return message, state, price, amt

def buy_limit_order(api, coin, price, amt):
    message = ""
    uuid = "none"
    result = {"uuid":""}
    try:
        result = api.buy_limit_order(coin, price, amt)
    except:
        message = f"{sys.exc_info()}"

    try:
        message = result["error"]["message"]
    except:
        if message == "":
            message = "good"
            uuid = result["uuid"]
    return message, uuid

def sell_limit_order(api, coin, price, amt):
    message = ""
    uuid = "none"
    result = {"uuid":""}
    try:
        result = api.buy_limit_order(coin, price, amt)
    except:
        message = f"{sys.esc_info()}"
    
    # try:
    #     message = result["error"]["message"]
    # except:
    if message == "":
        message = "good"
        uuid = result["uuid"]
    return message, uuid

def buy_market_order(api, coin, price):
    message = ""
    uuid = "none"
    result = {"uuid":""}
    try:
        result = api.buy_market_order(coin, price)
    except:
        message = f"{sys.exc_info()}"

    try:
        message = result["error"]["message"]
    except:
        if message == "":
            message = "good"
            uuid = result["uuid"]
    return message, uuid

def sell_market_order(api, coin, amt):
    message = ""
    uuid = "none"
    result = {"uuid": ""}

    try:
        result = api.sell_market_order(coin, amt)
    except:
        message = f"{sys.exc_info()}"

    try:
        message = result["error"]["message"]
    except:
        if message == "":
            message = "good"
            uuid = result["uuid"]
    return message, uuid

def cancel_order(api, uuid):
    message = ""
    result = {"uuid":""}

    try:
        result = api.cancel_order(uuid)
    except:
        message = f"{sys.exc_info()}"

    try:
        message = result["error"]["message"]
    except:
        if message == "":
            message = "good"
            uuid = result["uuid"]
    return message, uuid

def cancel_all_order(api, coin):
    message = ""
    result = {"uuid":""}
    result_list = list()

    try:
        result_list = api.get_order(coin, state="wait")
    except:
        message = f"{sys.exc_info()}"

    try:
        message = result_list["error"]["message"]
    except:
        message = "good"
    
    if message == "good":
        for i in result_list:
            try:
                i = api.cancel_order(result["uuid"])
            except:
                message = f"{sys.exc_info()}"
                break
    return message

def take_profit(api, coin, buy_amt, buy_price, now_price, take_profit_rate):
    buy_price_tot = float(buy_amt) * float(buy_price)
    now_price_tot = float(buy_amt) * float(now_price)
    revenue_price = buy_price_tot * float(take_profit_rate)
    message = "not yet"
    uuid = "none"

    if now_price_tot - buy_price_tot > revenue_price:
        try:
            trade_price = "{:0.0{}f}".format(float(now_price), 0)
            trade_amt = "{:0.0{}f}".format(float(buy_amt), 4)
            message, uuid = api.sell_limit_order(coin, trade_price, trade_amt)
        except:
            message = f"{sys.exc_info()}"
    return message, uuid

def stop_loss(api, coin, buy_amt, buy_price, now_price, stop_loss_rate):
    buy_price_tot = float(buy_amt) * float(buy_price)
    now_price_tot = float(buy_amt) * float(now_price)
    stop_price = buy_price_tot * float(stop_loss_rate)
    message = "not yet"
    uuid = "none"

    if buy_price_tot - now_price_tot > stop_price:
        try:
            trade_price = "{:0.0{}f}".format(float(now_price), 0)
            trade_amt = "{:0.0{}f}".format(float(buy_amt), 4)
            message, uuid = api.sell_limit_order(coin, trade_price, trade_amt)
        except:
            message= f"{sys.exc_info()}"
    return message, uuid

def get_web_m_data(url):
    df = pd.DataFrame()
    cols = {"timestamp", "openingPrice", "highPrice", "lowPrice", "tradePrice", "candleAccTradeVolume"}
    columns = {"timestamp":'t', "openingPrice":'o', "highPrice":'h', "lowPrice":'l', "tradePrice":'c', "candleAccTradeVolume":'v'}

    for i in range(3):
        try:
            res = requests.get(url, timeout=3)
            df_t = pd.read_json(res.content)
            df_t = df_t[cols].sort_values(by="timestamp", ascending=True)
            df = df_t.rename(columns=columns)
            break
        except:
            print("error")
        time.sleep(1)
    return df

def log(message):
    f = open("./logs/logs.txt", 'a')
    f.write(f"{message}\n")
    print(message)
    f.close

def get_time(time, arg):
    time = float(time)
    KST = datetime.timezone(datetime.timedelta(hours=9))
    dt = datetime.datetime.fromtimestamp(time, tz=KST)
    return str(dt.strftime(f"%{arg}"))

def check_open_cnt(check_data, amt_list):
    i = 1
    for j in amt_list:
        if round(float(check_data), 0) == round(float(j), 0):
            return i
        i += 1
    return i

def get_buy_amt_list(buy_amt_unit, buy_cnt_limit, increase_rate):
    buy_amt = 0
    buy_amt_list = [0.0]
    for i in range(buy_cnt_limit):
        amt = buy_amt_unit + buy_amt * increase_rate
        buy_amt = round(buy_amt + amt, 4)
        buy_amt_list.append(buy_amt)
    return buy_amt_list

def get_max_loss(close, buy_amt_unit, buy_cnt_limit, increase_rate, max_loss_rate):
    buy_amt = 0
    buy_price = 0
    for i in range(buy_cnt_limit):
        amt = buy_amt_unit + buy_amt * increase_rate
        buy_price = round(buy_price + close * amt, 4)
        buy_amt = round(buy_amt + amt, 4)
    return round(buy_price * max_loss_rate, 4)