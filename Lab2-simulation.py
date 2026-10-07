import pandas as pd
import matplotlib.pyplot as plt


COST, PRICE, SCRAP = 0.33, 0.50, 0.05      
MARGIN = PRICE - COST                      
DAYS = 10

raw = """
86043 23973 66248 97697 38244 50918 55441 51217 54786 04940
50807 51453 03462 61157 65366 61130 26204 15016 85665 97714
92168 82530 19271 86999 96499 12765 20926 25282 39119
36463 07331 54590 00546 03337 41583 46439 40173 46455
47097 78780 04210 87084 44484 75377 57753 41415 09890
80400 45972 44111 99708 45935 03694 81421 60170 58457
"""
digits = raw.replace(" ", "").replace("\n", "")
pairs = [int(digits[i:i + 2]) for i in range(0, len(digits) - 1, 2)]



RN_GROUPS = [(70, 90), (60, 80), (50, 40)]
RN_FOR_Q = {}
for g, qs in enumerate(RN_GROUPS):
    block = pairs[g * 2 * DAYS:(g + 1) * 2 * DAYS]
    for q in qs:
        RN_FOR_Q[q] = block


news_probs = {"Good": 0.35, "Fair": 0.45, "Poor": 0.20}

demand_values = [40, 50, 60, 70, 80, 90, 100]
demand_probs = {
    "Good": [0.03, 0.05, 0.15, 0.20, 0.35, 0.15, 0.07],
    "Fair": [0.10, 0.18, 0.40, 0.20, 0.08, 0.04, 0.00],
    "Poor": [0.44, 0.22, 0.16, 0.12, 0.06, 0.00, 0.00],
}


def build_table(labels, probs):
    """يحسب الـ Cumulative و الـ Range (RN من 01 إلى 00=100)"""
    rows, cum, prev = [], 0.0, 0
    for lab, p in zip(labels, probs):
        if p == 0:                       
            continue
        cum = round(cum + p, 2)
        hi = int(round(cum * 100))
        rows.append({"Value": lab, "Prob": p, "Cumulative": cum,
                     "Range": f"{prev + 1:02d}-{hi % 100:02d}" if hi == 100 else f"{prev + 1:02d}-{hi:02d}",
                     "lo": prev + 1, "hi": hi})
        prev = hi
    return pd.DataFrame(rows)


def lookup(table, rn):
    rn = 100 if rn == 0 else rn          
    row = table[(table.lo <= rn) & (rn <= table.hi)].iloc[0]
    return row["Value"]


news_table = build_table(list(news_probs), list(news_probs.values()))
demand_tables = {n: build_table(demand_values, p) for n, p in demand_probs.items()}

print("=" * 60)
print("News Type: Cumulative & Range")
print(news_table[["Value", "Prob", "Cumulative", "Range"]].to_string(index=False))
for n, t in demand_tables.items():
    print(f"\nDemand ({n}): Cumulative & Range")
    print(t[["Value", "Prob", "Cumulative", "Range"]].to_string(index=False))



def simulate(Q):
    rn = RN_FOR_Q[Q]
    rows = []
    for d in range(DAYS):
        rn_news, rn_dem = rn[2 * d], rn[2 * d + 1]
        news = lookup(news_table, rn_news)
        demand = lookup(demand_tables[news], rn_dem)

        sold = min(Q, demand)
        revenue = sold * PRICE
        cost = Q * COST
        lost = max(demand - Q, 0) * MARGIN
        scrap = max(Q - demand, 0) * SCRAP
        profit = revenue - cost - lost + scrap

        rows.append({
            "Day": d + 1, "RN for NT": f"{rn_news:02d}", "News Type": news,
            "RN for Demand": f"{rn_dem:02d}", "Demand": demand,
            "Revenue from Sales": round(revenue, 2), "Cost of NPs": round(cost, 2),
            "Lost Profit": round(lost, 2), "Scrap Revenue": round(scrap, 2),
            "Daily Profit": round(profit, 2),
        })
    return pd.DataFrame(rows)


results = {}
summary = []
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)

for Q in [70, 90, 60, 80, 50, 40]:                
    df = simulate(Q)
    results[Q] = df
    totals = {
        "Q": Q,
        "Total Revenue": df["Revenue from Sales"].sum(),
        "Total Cost": df["Cost of NPs"].sum(),
        "Total Lost Profit": df["Lost Profit"].sum(),
        "Total Scrap": df["Scrap Revenue"].sum(),
        "Total Profit": df["Daily Profit"].sum(),
    }
    summary.append(totals)

    print("\n" + "=" * 60)
    print(f"Simulation for Q = {Q} newspapers/day")
    print(df.to_string(index=False))
    print(f"Total Cost = {totals['Total Cost']:.2f} | "
          f"Total Profit = {totals['Total Profit']:.2f}")

summary_df = pd.DataFrame(summary).sort_values("Q").round(2).reset_index(drop=True)
print("\n" + "=" * 60)
print("Summary of all cases")
print(summary_df.to_string(index=False))

best = summary_df.loc[summary_df["Total Profit"].idxmax()]
print(f"\n>>> Best order quantity: Q = {int(best.Q)}  with total profit = {best['Total Profit']:.2f}")


with pd.ExcelWriter("newsboy_results.xlsx") as xw:
    for Q in sorted(results):
        results[Q].to_excel(xw, sheet_name=f"Q={Q}", index=False)
    summary_df.to_excel(xw, sheet_name="Summary", index=False)




colors = ["#2a9d8f" if q == best.Q else "#8ab6d6" for q in summary_df["Q"]]
fig, ax = plt.subplots(figsize=(9, 5.5))
bars = ax.bar(summary_df["Q"].astype(str), summary_df["Total Profit"], color=colors)
for b, v in zip(bars, summary_df["Total Profit"]):
    ax.text(b.get_x() + b.get_width() / 2, v, f"{v:.1f}", ha="center",
            va="bottom" if v >= 0 else "top", fontweight="bold")
ax.plot(summary_df["Q"].astype(str), summary_df["Total Profit"], "o--", color="#e76f51", label="Profit trend")
ax.set_xlabel("Order quantity Q (newspapers per day)")
ax.set_ylabel("Total profit over 10 days")
ax.set_title("Newsboy simulation: total profit for each order quantity")
ax.axhline(0, color="black", linewidth=0.8)
ax.legend()
plt.tight_layout()
plt.savefig("profit_comparison.png", dpi=150)
plt.show()
