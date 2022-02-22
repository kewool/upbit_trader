import pandas as pd
import numpy as np
import requests
import csv
import time
import random
import datetime
import os

coin = "KRW-XRP"
date = "2022-02-21T00:00:00"


cols = ["timestamp", "openingPrice", "highPrice", "lowPrice", "tradePrice", "candleAccTradeVolume"]

# https://crix-api-cdn.upbit.com/v1/crix/candles/minutes/30?code=CRIX.UPBIT.KRW-STRK&count=1000&to=2022-02-20T11:20:09Z
df = pd.DataFrame()

for i in range(0, 500):
    url = f"https://crix-api-cdn.upbit.com/v1/crix/candles/minutes/1?code=CRIX.UPBIT.{coin}&count=4000&to={date}.000Z"
    page = requests.get(url)
    data = pd.read_json(page.content)[cols]

    df = df.append(data)

    date = data.tail(1)["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%S").values[0]


    #delay = random.choice([1.2,1.4,1.6,1.8])
    #time.sleep(delay)
    #print(i, end=", ")

df.reset_index()
df.to_csv(f"./data/{coin}.csv", index=False)
