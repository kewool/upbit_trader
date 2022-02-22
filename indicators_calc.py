from trading import *

coin = "KRW-XRP"
df = pd.read_csv(f"./data/{coin}.csv")
df = df.sort_values(by="timestamp", ascending=True)
columns = {"timestamp":'t', "openingPrice":'o', "highPrice":'h', "lowPrice":'l', "tradePrice":'c', "candleAccTradeVolume":'v'}
df = df.rename(columns=columns)

df = add_sma(df, df['c'], 7, 25, 99)
df = add_wma(df, df['c'], 7, 25, 99)
df = add_ema(df, df['c'], 7, 25, 99)
df = add_macd(df, df['c'], 26, 12, 9)
df = add_rsi(df, df['c'], 6, 12, 24)
df = add_stochrsi(df, df['c'], 14, 3, 3)
df = add_bb(df, df['c'], 20, 2)
df = add_vwap(df, df['h'], df['l'], df['c'], df['v'], 14)
df = df.dropna()

df.to_csv(f"./data/{coin}-index.csv", index=False)