from trading import *
import random as rand
from bayes_opt import BayesianOptimization

np.seterr(divide='ignore', invalid='ignore')

coin = "KRW-XRP"
df = pd.read_csv(f"./data/{coin}-index.csv")

def black_box(revenue_rate, max_loss_rate, increase_rate, buy_cnt_limit, buy_amt_unit):
    config = {
        "revenue_rate":revenue_rate,
        "max_loss_rate":max_loss_rate,
        "increase_rate":increase_rate,
        "buy_cnt_limit":buy_cnt_limit,
        "buy_amt_unit":buy_amt_unit
    }
    return run_test(df, config)

pbounds = {
    "revenue_rate":(0.004795200288603781, 0.004795200288603781),
    "max_loss_rate":(0.2965237753456481, 0.2965237753456481),
    "increase_rate":(0.2000292756278028, 0.2000292756278028),
    "buy_cnt_limit":(1, 5),
    "buy_amt_unit":(1, 10)
    # "revenue_rate":(0.004795200288603781, 0.004795200288603781),
    # "max_loss_rate":(0.2965237753456481, 0.2965237753456481),
    # "increase_rate":(0.2000292756278028, 0.2000292756278028),
    # "buy_cnt_limit":(2, 2),
    # "buy_amt_unit":(7, 7)
    # "revenue_rate":0.004795200288603781,
    # "max_loss_rate":0.2965237753456481,
    # "increase_rate":0.2000292756278028,
    # "buy_cnt_limit":17.025739384927544,
    # "buy_amt_unit":31.042185615538518
}

optimizer = BayesianOptimization(f=black_box, pbounds=pbounds, random_state=1)

optimizer.maximize(init_points=5, n_iter=50)

target_list = []

for i, k in enumerate(optimizer.res):
    target_list.append(f"{k['target']}, {i}")
target_list.sort(reverse=True)
print(target_list)

print(optimizer.res[int(input())])