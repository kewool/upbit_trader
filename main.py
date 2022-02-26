import upbitopenapi.config as conf
from trading import *

coin = "KRW-XRP"
#df = pd.read_csv(f"./data/{coin}-index.csv")

access = conf.G_API_KEY
secret = conf.G_SECRET_KEY
api = pyupbit.Upbit(access, secret)
url = f"https://crix-api-cdn.upbit.com/v1/crix/candles/minutes/1?code=CRIX.UPBIT.{coin}&count=200"

# revenue_rate = 0.004795200288603781
# max_loss_rate = 0.2965237753456481
# increase_rate = 0.2000292756278028
# buy_cnt_limit = 1
# buy_amt_unit = 1

revenue_rate = 0.002
max_loss_rate = 0.003
increase_rate = 0.0
buy_cnt_limit = 2
buy_amt_unit = 7

buy_amt_list = []
buy_amt_list = get_buy_amount(buy_amt_unit, buy_cnt_limit, increase_rate)
max_loss = 0

trade_flag = 1
sleep_time = 0.2

order_uuid = ""
profit_uuid = ""
stop_uuid = ""

log("start")

message = cancel_all_order(api, coin)
if message != "good":
    log(f"[{time.time()}]cancel_all_order error message: {message}")

while True:
    check_sec = get_time(time.time(), 'S')

    if check_sec in ("01", "02"):
        df = get_web_m_data(url)
        time.sleep(sleep_time)

        df = add_wma(df, df['c'], 7, 99)
        df = add_vwap(df, df['h'], df['l'], df['c'], df['v'], 14)

        df_last = df.iloc[df.shape[0]-1:]
        wma7 = df_last["wma7"].values[0]
        wma99 = df_last["wma99"].values[0]
        vwap = df_last["vwap"].values[0]
        
        trade_flag = 0
    
    if trade_flag == 0 and check_sec in ("59", "00"):
        trade_flag = 1
        if order_uuid != "":
            message, status, price, amt = get_order_status(api, order_uuid)
            if message != "good":
                log(f"[{time.time()}] get_order_status error message: {message}, uuid: {order_uuid}")
                continue
            if status == "done":
                order_uuid = ""
            if status == "wait":
                message, result = cancel_order(api, order_uuid)
                if message != "good":
                    log(f"[{time.time()}] cancel_order error message: {message}, uuid: {order_uuid}")
                    continue
                time.sleep(sleep_time)
        
        message, buy_amt, buy_price = get_balance(api, coin)
        if message != "good":
            log(f"[{time.time()}] get_balance error message: {message}")
            continue
        time.sleep(sleep_time)

        message, result = get_current_price(coin)
        if message != "good":
            log(f"[{time.time()}] get_current_price error message: {message}")
            continue
        close = float(result)

        buy_cnt = check_open_cnt(buy_amt, buy_amt_list)
        log(f"[{time.time()}] close: {round(close, 4)}, vwap: {round(vwap, 4)}, wma7: {round(wma7, 4)}, wma99: {round(wma99, 4)}, buy_cnt: {buy_cnt - 1}, buy_cnt_limit: {buy_cnt_limit}")
        time.sleep(sleep_time)

        if buy_cnt <= buy_cnt_limit and close < vwap and close < wma7 and wma7 > wma99:
            order_buy_amt = buy_amt_unit + float(buy_amt) * increase_rate

            message, result = get_current_price(coin)
            if message != "good":
                log(f"[{time.time()}] get_current_price error message: {message}")
                continue
            
            trade_price = "{:0.0{}f}".format(float(result), 0)
            trade_amt = "{:0.0{}f}".format(order_buy_amt, 4)
            print(trade_price)
            print(trade_amt)
            message, order_uuid = buy_limit_order(api, coin, trade_price, trade_amt)
            if message != "good":
                log(f"[{time.time()}] buy_limit_order error {message}")
                order_uuid = ""
                continue
            trade_flag = 1
            log(f"[{time.time()}] buy coin uuid: {order_uuid}, v: {round(vwap, 4)}, c: {close}, p: {trade_price}, a: {trade_amt}, m: {message}")
            time.sleep(sleep_time)

    if check_sec in ("10", "20", "30", "40", "50"):
        if profit_uuid != "":
            message, status, price, amt = get_order_status(api, coin, profit_uuid)
            if message != "good":
                log(f"[{time.time()}] get_order_status error message: {message} uuid: {profit_uuid}")
                continue

            if status == "done":
                profit_uuid = ""

            if status == "wait":
                message, result = cancel_order(api, profit_uuid)
                if message != "good":
                    log(f"[{time.time()}] cancel_order error message: {message}, uuid: {profit_uuid}")
                    continue
                time.sleep(sleep_time)

        message, buy_amt, buy_price = get_balance(api, coin)
        if message != "good":
            log(f"[{time.time()}] get_balance error message: {message}")
            continue
        time.sleep(sleep_time)

        if float(buy_amt) > 0:
            message, result = get_current_price(coin)
            if message != "good":
                log(f"[{time.time()}] get_current_price error message: {message}")
                continue

            message, uuid = take_profit(api, coin, buy_amt, buy_price, result, revenue_rate)
            if message == "good":
                profit_uuid = uuid
                log(f"[{time.time()}] take profit uuid: {profit_uuid}, buy_amt: {buy_amt}, buy_price: {buy_price}, message: {message}")
            time.sleep(sleep_time)

        if stop_uuid != "":
            message, stauts, price, amt = get_order_status(api, coin, stop_uuid)
            if message != "good":
                log(f"[{time.time()}] get_order_status error message: {message}, uuid: {stop_uuid}")
                continue

            if status == "done":
                stop_uuid = ""
            
            if status == "wait":
                message, result = cancel_order(api, coin)
                if message != "good":
                    log(f"[{time.time()}] cancel_order error message: {message}, uuid: {stop_uuid}")
                    continue
                time.sleep(sleep_time)
        
        message, buy_amt, buy_price = get_balance(api, coin)
        if message != "good":
            log(f"[{time.time()}] get_balance error message: {message}")
            continue
        time.sleep(sleep_time)

        if float(buy_amt) > 0:
            message, result = get_current_price(coin)
            if message != "good":
                log(f"[{time.time()}] get_current_price error message: {message}")
                continue

            message, uuid = stop_loss(api, coin, buy_amt, buy_price, float(result), max_loss_rate)
            if message == "good":
                stop_uuid = uuid
                log(f"[{time.time()}] stop loss uuid: {stop_uuid}, buy_amt: {buy_amt}, buy_price: {buy_price}, now_price: {result}, message: {message}")
            time.sleep(sleep_time)
    time.sleep(1)

