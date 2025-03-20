"""
Copied from a post on LinkedIn by PyQuant News.
The code was all in a series of screenshots...
There is probably a bit missing, since S1 and S2 are not defined.
And probably other bugs as well.
"""

import numpy as np
import pandas as pd

import statsmodels.api as sm
from statsmodels.tsa.stattools import coint
from statsmodels.regression.rolling import RollingOLS

import yfinance as yf
import seaborn
import matplotlib.pyplot as plt


start = "2014-01-01"
end = "2015-01-01"

file_name = f"stock_prices_{start}_{end}.csv"

symbol_list = ["META", "AMZN", "AAPL", "NFLX", "GOOG"]

try:
    df = pd.read_csv(file_name, index_col="Date")
except FileNotFoundError:
    df = yf.download(
        tickers=symbol_list,
        start=start,
        end=end,
    )["Close"]
    df.to_csv(file_name)


print(df)
print("data.shape", df.shape)
print("data.keys()", df.keys())


def find_cointegrated_pairs(df):
    n = df.shape[1]  # Number of columns.  (Date column is the index.)
    score_matrix = np.zeros((n, n))
    pvalue_matrix = np.ones((n, n))
    keys = df.keys()
    cointegrated_pairs = []

    for i in range(n):
        for j in range(i+1, n):
            Series1 = df[keys[i]]
            Series2 = df[keys[j]]
            score, pvalue, crit_vals = coint(Series1, Series2)
            score_matrix[i, j] = score
            pvalue_matrix[i, j] = pvalue

            if pvalue < 0.05:
                cointegrated_pairs.append((keys[i], keys[j]))

    return score_matrix, pvalue_matrix, cointegrated_pairs


scores, pvalues, pairs = find_cointegrated_pairs(df)

print(scores)
print(pvalues)
print(pairs)

seaborn.heatmap(
    pvalues,
    xticklabels=df.keys(),
    yticklabels=df.keys(),
    cmap='RdYlGn_r',
    mask=(pvalues >= 0.10)
)
plt.savefig("heatmap.png")
plt.clf()

# Make regression plot of Amazon and Google prices.
S2 = df["GOOG"]
S1 = df["AMZN"]

S1 = sm.add_constant(S1)
results = sm.OLS(S2, S1).fit()
S1 = S1.AMZN
b = results.params['AMZN']
b0 = results.params['const']
print(b, b0)

plt.scatter(S1, S2)
min_x = S1.min()
max_x = S1.max()
x = np.arange(start=min_x, stop=max_x, step=0.1)
y = b * x + b0
plt.plot(x, y, 'red')
plt.savefig("regression.png")
print(min_x, max_x)


# spread = S2 - b * S1
#
# print("spread")
# print(spread)
# print(results.params)
#
#
# def zscore(series):
#     return (series - series.mean()) / np.std(series)
#
#
# zscore(spread).plot()
#
# plt.axhline(zscore(spread).mean(), color='black')
# plt.axhline(1.0, color='red', linestyle='--')
# plt.axhline(-1.0, color='green', linestyle='--')
# plt.legend(['Spread z-score', 'Mean', '+1', '-1'])
#
#
# # Create a DataFrame with the signal and position size in the pair.
# trades = pd.concat([zscore(spread), S2 - b * S1], axis=1)
# trades.columns = ["signal", "position"]
#
# # Add a long and short position at the z-score levels
# trades["side"] = 0.0
# trades.loc[trades.signal <= -1, "side"] = 1
# trades.loc[trades.signal >= 1, "side"] = -1
#
# returns = trades.position.pct_change() * trades.side
# returns.cumsum().plot()
#
