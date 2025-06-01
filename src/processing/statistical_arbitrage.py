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


temp_folder = "../temp/"

start = "2014-01-01"
end = "2015-01-01"

file_name = temp_folder + f"stock_prices_{start}_{end}.csv"

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
                cointegrated_pairs.append((keys[i], keys[j], pvalue))

    cointegrated_pairs.sort(key=lambda x: x[2])

    return score_matrix, pvalue_matrix, cointegrated_pairs


scores, pvalues, pairs = find_cointegrated_pairs(df)

# print(scores)
# print(pvalues)
print(pairs)

seaborn.heatmap(
    pvalues,
    xticklabels=df.keys(),
    yticklabels=df.keys(),
    cmap='RdYlGn_r',
    mask=(pvalues >= 0.10)
)
plt.savefig(temp_folder + "heatmap.png")
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
plt.savefig(temp_folder + "regression.png")
plt.clf()
print(min_x, max_x)

# spread = S2 - b * S1  # Difference between actual Google price and Google price estimated from regression line.
estimated_S2 = b * S1 + b0
spread = S2 - estimated_S2
plt.plot(spread)
plt.savefig(temp_folder + "spread.png")
plt.clf()
print("spread")


# def zscore(series):
#     return (series - series.mean()) / np.std(series)

zscore_spread = (spread - spread.mean()) / np.std(spread)

# zscore(spread).plot()

zscore_spread.plot()

plt.axhline(zscore_spread.mean(), color='black')
plt.axhline(1.0, color='red', linestyle='--')
plt.axhline(-1.0, color='green', linestyle='--')
plt.legend(['Spread z-score', 'Mean', '+1', '-1'])
plt.savefig(temp_folder + "zscore_spread.png")
plt.clf()


# Create a DataFrame with the signal and position size in the pair.
position = S2 - b * S1
trades = pd.concat([position, zscore_spread], axis=1)
trades.columns = ["position", "signal"]

# Add a long and short position at the z-score levels
trades["side"] = 0.0
trades.loc[trades.signal <= -1, "side"] = 1
trades.loc[trades.signal >= 1, "side"] = -1

# PyQuant's original calculation of returns makes no sense...
# trades["returns"] = trades.position.pct_change() * trades.side
# trades["cum_returns"] = trades.returns.cumsum()

# Build a better trading strategy...
# Want a signal to buy as soon as 'side' is 1, and sell as soon as 'side' is -1.


def calculate_short_long_signal(df):

    return_sign = 0

    position_sign = []
    for x in df.side:
        if x == 1:
            return_sign = 1
        elif x == -1:
            return_sign = -1

        position_sign.append(return_sign)

    df["return_sign"] = position_sign

    return df


trades = calculate_short_long_signal(trades)
trades["position_diff"] = trades.position.diff()
trades["returns"] = trades.position_diff * trades.return_sign.shift()  # Try shift() to flip sign the day after zscore goes to -1.
trades["cum_returns"] = trades.returns.cumsum()

first_position = trades.loc[trades.return_sign != 0].iloc[0]
opening_position = first_position.position

print("Opening position", opening_position)

trades["traded_returns"] = trades.cum_returns + opening_position
trades["fractional_return"] = (trades.cum_returns + opening_position) / opening_position

# print(trades)
trades.to_csv(temp_folder + "trades.csv")

fig, ax1 = plt.subplots()
ax1.plot(trades.position)
ax1.plot(trades.traded_returns)
plt.savefig(temp_folder + "traded_returns.png")
plt.clf()

fig, ax1 = plt.subplots()
ax1.plot(trades.position)
ax1.set_xlabel("Date")

ax2 = ax1.twinx()
ax2.plot(trades.fractional_return, color='red')
# ax2.plot(trades.returns, color='red')
# ax2.plot(trades.cum_returns, color='green')
plt.savefig(temp_folder + "trading.svg")
plt.clf()

# returns = trades.position.pct_change() * trades.side
# returns.plot()
# plt.savefig(temp_folder + "returns.png")
# plt.clf()
# trades.position.plot()
# plt.savefig(temp_folder + "position.png")
# plt.clf()
#
# returns.cumsum().plot()
# plt.savefig(temp_folder + "cumulative_returns.png")
# plt.clf()
