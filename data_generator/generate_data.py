"""
PriceScope - synthetic data generator
Fictional beverage retailer: Berliner Getraenkehandel GmbH
~50 stores in Berlin/Brandenburg, 2 years of daily POS sales.

Baked-in patterns (so downstream analysis finds real signal):
- Category seasonality (beer/water/soft drinks peak in summer, spirits in December)
- Weekday effects, Sunday closure (German retail law)
- 1-3 list price changes per product over 2 years (SCD2 material)
- Promo calendar with discounts + display uplift
- True price elasticity per category (log-log demand model)
- Competitor price feeds (JSON, monthly files) tracking own prices with noise

Outputs (relative to --out):
  master/products.csv, master/stores.csv, master/price_history.csv, master/promotions.csv
  sales/pos_sales_YYYY_MM.csv        (monthly partitions, ~1M rows total)
  competitor/competitor_prices_YYYY_MM.json
"""

import argparse
import json
import os

import numpy as np
import pandas as pd

SEED = 42
START = "2024-07-01"
END = "2026-06-30"  # 2 full years
N_STORES = 50
N_PRODUCTS = 300
ASSORTMENT_SIZE = 80  # products carried per store

CATEGORIES = {
    # category: (share of products, base daily demand, elasticity, summer_amp, winter_amp)
    "Bier": (0.30, 6.0, -1.3, 0.45, 0.0),
    "Wasser": (0.20, 8.0, -0.6, 0.55, 0.0),
    "Softdrinks": (0.20, 5.0, -1.0, 0.35, 0.0),
    "Saft": (0.10, 3.0, -0.9, 0.10, 0.05),
    "Wein": (0.12, 2.0, -0.8, 0.0, 0.30),
    "Spirituosen": (0.08, 1.2, -0.7, 0.0, 0.50),
}

BRANDS = {
    "Bier": ["Berliner Kindl", "Schultheiss", "Potsdamer Rex", "Spree Braeu", "Hopfenwerk", "Kiez Pils"],
    "Wasser": ["Brandenburger Quelle", "Spreewasser", "Havel Still", "ClaraQuell"],
    "Softdrinks": ["BrauseBar", "Kiez Cola", "Limo Luise", "Sprudelzeit"],
    "Saft": ["Obstgut Werder", "SaftWerk", "Gartenfrucht"],
    "Wein": ["Weingut Elbtal", "Rebenhof", "Vino Casa Import"],
    "Spirituosen": ["Adler Destille", "Nordbrand", "Kornhaus"],
}

VARIANTS = {
    "Bier": ["Pils", "Helles", "Weizen", "Radler", "Alkoholfrei", "Export"],
    "Wasser": ["Classic", "Medium", "Still", "Lemon"],
    "Softdrinks": ["Cola", "Orange", "Zitrone", "Mate", "Cola Zero"],
    "Saft": ["Apfel", "Orange", "Multivitamin", "Rhabarber"],
    "Wein": ["Riesling", "Grauburgunder", "Merlot", "Rose"],
    "Spirituosen": ["Korn", "Gin", "Kraeuterlikoer", "Vodka"],
}

UNIT_SIZES = {
    "Bier": ["0.5L Flasche", "0.33L Flasche", "6x0.5L", "20x0.5L Kasten"],
    "Wasser": ["1.5L PET", "12x0.7L Kasten", "0.75L Glas"],
    "Softdrinks": ["1.0L PET", "1.5L PET", "6x1.0L"],
    "Saft": ["1.0L Tetra", "0.75L Glas"],
    "Wein": ["0.75L Flasche"],
    "Spirituosen": ["0.7L Flasche"],
}

PRICE_RANGES = {  # (min, max) list price by dominant unit
    "Bier": (0.79, 18.99),
    "Wasser": (0.45, 9.49),
    "Softdrinks": (0.99, 8.99),
    "Saft": (1.29, 4.99),
    "Wein": (3.99, 14.99),
    "Spirituosen": (6.99, 24.99),
}

BERLIN_DISTRICTS = ["Pankow", "Mitte", "Neukoelln", "Charlottenburg", "Spandau",
                    "Lichtenberg", "Steglitz", "Treptow", "Reinickendorf", "Marzahn"]
BRANDENBURG_TOWNS = ["Potsdam", "Oranienburg", "Bernau", "Falkensee", "Koenigs Wusterhausen",
                     "Ludwigsfelde", "Strausberg", "Teltow", "Eberswalde", "Brandenburg a.d.H."]


def make_stores(rng):
    rows = []
    for i in range(1, N_STORES + 1):
        is_berlin = rng.random() < 0.6
        if is_berlin:
            city, region = "Berlin", "Berlin"
            name = f"GH Markt Berlin-{rng.choice(BERLIN_DISTRICTS)} {i:03d}"
        else:
            city = rng.choice(BRANDENBURG_TOWNS)
            region = "Brandenburg"
            name = f"GH Markt {city} {i:03d}"
        fmt = rng.choice(["Standard", "Kompakt", "XL"], p=[0.6, 0.25, 0.15])
        size_factor = {"Kompakt": 0.6, "Standard": 1.0, "XL": 1.7}[fmt]
        size_factor *= float(rng.lognormal(0, 0.15))
        opened = pd.Timestamp("2005-01-01") + pd.Timedelta(days=int(rng.integers(0, 6500)))
        rows.append({
            "store_id": f"S{i:03d}", "store_name": name, "city": city, "region": region,
            "store_format": fmt, "opened_date": opened.date().isoformat(),
            "_size_factor": round(size_factor, 3),
        })
    return pd.DataFrame(rows)


def make_products(rng):
    rows, pid = [], 1
    for cat, (share, base_d, elast, s_amp, w_amp) in CATEGORIES.items():
        n = round(N_PRODUCTS * share)
        for _ in range(n):
            brand = rng.choice(BRANDS[cat])
            variant = rng.choice(VARIANTS[cat])
            size = rng.choice(UNIT_SIZES[cat])
            lo, hi = PRICE_RANGES[cat]
            list_price = round(float(rng.uniform(lo, hi)), 2)
            # margin between 18% and 42% of price
            cost = round(list_price * float(rng.uniform(0.58, 0.82)), 2)
            ean = f"40{rng.integers(10**10, 10**11 - 1)}"
            rows.append({
                "product_id": f"P{pid:04d}", "ean": ean,
                "product_name": f"{brand} {variant} {size}",
                "category": cat, "brand": brand, "unit_size": size,
                "unit_cost": cost, "initial_list_price": list_price,
                "_base_demand": base_d, "_elasticity": elast,
                "_summer_amp": s_amp, "_winter_amp": w_amp,
            })
            pid += 1
    return pd.DataFrame(rows)


def make_price_history(products, dates, rng):
    """1-3 price changes per product over the horizon -> SCD2-style table."""
    rows = []
    for _, p in products.iterrows():
        n_changes = int(rng.integers(1, 4))
        change_days = np.sort(rng.choice(np.arange(60, len(dates) - 30), size=n_changes, replace=False))
        price = p["initial_list_price"]
        valid_from = dates[0]
        for cd in change_days:
            valid_to = dates[cd] - pd.Timedelta(days=1)
            rows.append({"product_id": p["product_id"], "list_price": round(price, 2),
                         "valid_from": valid_from.date().isoformat(),
                         "valid_to": valid_to.date().isoformat()})
            # mostly increases (inflation), sometimes decreases
            pct = float(rng.uniform(0.02, 0.09)) * (1 if rng.random() < 0.75 else -1)
            price = max(0.39, price * (1 + pct))
            valid_from = dates[cd]
        rows.append({"product_id": p["product_id"], "list_price": round(price, 2),
                     "valid_from": valid_from.date().isoformat(), "valid_to": "9999-12-31"})
    return pd.DataFrame(rows)


def make_promotions(products, dates, rng):
    """Weekly promo slots: each week ~8% of products on promo (Mon-Sun)."""
    rows, promo_id = [], 1
    week_starts = pd.date_range(dates[0], dates[-1], freq="W-MON")
    pids = products["product_id"].to_numpy()
    for ws in week_starts:
        n_promo = max(1, int(len(pids) * 0.08))
        chosen = rng.choice(pids, size=n_promo, replace=False)
        for pr in chosen:
            rows.append({
                "promo_id": f"PR{promo_id:05d}", "product_id": pr,
                "start_date": ws.date().isoformat(),
                "end_date": (ws + pd.Timedelta(days=6)).date().isoformat(),
                "discount_pct": int(rng.choice([10, 15, 20, 25], p=[0.35, 0.3, 0.25, 0.1])),
            })
            promo_id += 1
    return pd.DataFrame(rows)


def daily_price_matrix(products, price_history, promotions, dates):
    """(n_products, n_days) effective shelf price + promo flag matrix."""
    n_p, n_d = len(products), len(dates)
    date_index = pd.Series(np.arange(n_d), index=dates)
    pid_index = {pid: i for i, pid in enumerate(products["product_id"])}

    list_price = np.zeros((n_p, n_d))
    ph = price_history.copy()
    ph["valid_from"] = pd.to_datetime(ph["valid_from"])
    ph["valid_to"] = pd.to_datetime(ph["valid_to"].replace("9999-12-31", END))
    for _, r in ph.iterrows():
        i = pid_index[r["product_id"]]
        a = date_index.get(max(r["valid_from"], dates[0]), 0)
        b = date_index.get(min(r["valid_to"], dates[-1]), n_d - 1)
        list_price[i, a:b + 1] = r["list_price"]

    promo_flag = np.zeros((n_p, n_d), dtype=bool)
    discount = np.zeros((n_p, n_d))
    pr = promotions.copy()
    pr["start_date"] = pd.to_datetime(pr["start_date"])
    pr["end_date"] = pd.to_datetime(pr["end_date"])
    for _, r in pr.iterrows():
        i = pid_index[r["product_id"]]
        a = date_index.get(max(r["start_date"], dates[0]), 0)
        b = date_index.get(min(r["end_date"], dates[-1]), n_d - 1)
        promo_flag[i, a:b + 1] = True
        discount[i, a:b + 1] = r["discount_pct"] / 100.0

    shelf_price = np.round(list_price * (1 - discount), 2)
    return list_price, shelf_price, promo_flag


def seasonality_matrix(products, dates):
    """(n_products, n_days) seasonal demand multiplier."""
    doy = dates.dayofyear.to_numpy()
    summer = np.exp(-0.5 * ((doy - 200) / 45.0) ** 2)          # peak mid-July
    winter = np.exp(-0.5 * ((np.minimum(doy, 365 - doy + 1)) / 25.0) ** 2)  # peak around New Year/Dec
    s_amp = products["_summer_amp"].to_numpy()[:, None]
    w_amp = products["_winter_amp"].to_numpy()[:, None]
    return 1.0 + s_amp * summer[None, :] + w_amp * winter[None, :]


def weekday_vector(dates):
    wd = dates.dayofweek.to_numpy()  # Mon=0 .. Sun=6
    factors = np.array([0.85, 0.85, 0.9, 1.0, 1.35, 1.45, 0.0])  # Sunday closed
    return factors[wd]


def generate_sales(stores, products, dates, list_price, shelf_price, promo_flag, rng, out_dir):
    n_s, n_p, n_d = len(stores), len(products), len(dates)
    base = products["_base_demand"].to_numpy()[:, None]
    elast = products["_elasticity"].to_numpy()[:, None]
    season = seasonality_matrix(products, dates)
    wkday = weekday_vector(dates)[None, :]

    ref = products["initial_list_price"].to_numpy()[:, None]
    price_effect = np.power(np.maximum(shelf_price, 0.01) / ref, elast)
    display_boost = np.where(promo_flag, 1.25, 1.0)

    lam_pd = base * season * wkday * price_effect * display_boost  # (n_p, n_d)

    # store assortments
    assort = np.zeros((n_s, n_p), dtype=bool)
    for si in range(n_s):
        assort[si, rng.choice(n_p, size=ASSORTMENT_SIZE, replace=False)] = True
    size_f = stores["_size_factor"].to_numpy()

    store_ids = stores["store_id"].to_numpy()
    product_ids = products["product_id"].to_numpy()

    months = pd.period_range(dates[0], dates[-1], freq="M")
    total_rows = 0
    os.makedirs(out_dir, exist_ok=True)
    for m in months:
        d_mask = np.asarray(dates.to_period("M") == m)
        d_idx = np.where(d_mask)[0]
        chunks = []
        for si in range(n_s):
            p_idx = np.where(assort[si])[0]
            lam = lam_pd[np.ix_(p_idx, d_idx)] * size_f[si]
            noise = rng.lognormal(0, 0.25, size=lam.shape)
            units = rng.poisson(lam * noise)
            pp, dd = np.nonzero(units)
            if len(pp) == 0:
                continue
            chunks.append(pd.DataFrame({
                "sale_date": dates[d_idx[dd]].date,
                "store_id": store_ids[si],
                "product_id": product_ids[p_idx[pp]],
                "units_sold": units[pp, dd],
                "unit_price": shelf_price[p_idx[pp], d_idx[dd]],
                "promo_flag": promo_flag[p_idx[pp], d_idx[dd]].astype(int),
            }))
        df = pd.concat(chunks, ignore_index=True).sort_values(["sale_date", "store_id", "product_id"])
        fname = os.path.join(out_dir, f"pos_sales_{m.year}_{m.month:02d}.csv")
        df.to_csv(fname, index=False)
        total_rows += len(df)
        print(f"  {os.path.basename(fname)}: {len(df):,} rows")
    return total_rows


def generate_competitor_feed(products, dates, list_price, rng, out_dir):
    """Monthly JSON: 2 competitors quote weekly prices for ~60% of assortment (matched by EAN)."""
    os.makedirs(out_dir, exist_ok=True)
    competitors = ["TrinkGut Discount", "GetraenkeStar"]
    covered = rng.random(len(products)) < 0.6
    months = pd.period_range(dates[0], dates[-1], freq="M")
    date_index = pd.Series(np.arange(len(dates)), index=dates)
    for m in months:
        week_starts = [d for d in pd.date_range(m.start_time, m.end_time, freq="W-MON") if d in date_index.index]
        records = []
        for comp_i, comp in enumerate(competitors):
            bias = 0.97 if comp_i == 0 else 1.02  # discounter undercuts, other slightly above
            for ws in week_starts:
                di = date_index[ws]
                noise = rng.normal(1.0, 0.03, size=len(products))
                prices = np.round(list_price[:, di] * bias * noise, 2)
                for pi in np.where(covered)[0]:
                    records.append({
                        "competitor": comp,
                        "ean": products.iloc[pi]["ean"],
                        "price": float(max(prices[pi], 0.29)),
                        "observed_at": ws.date().isoformat(),
                    })
        fname = os.path.join(out_dir, f"competitor_prices_{m.year}_{m.month:02d}.json")
        with open(fname, "w") as f:
            json.dump({"source": "price-scraper-v2", "records": records}, f)
        print(f"  {os.path.basename(fname)}: {len(records):,} records")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="../data")
    args = ap.parse_args()

    rng = np.random.default_rng(SEED)
    dates = pd.date_range(START, END, freq="D")
    print(f"Horizon: {START} .. {END} ({len(dates)} days)")

    stores = make_stores(rng)
    products = make_products(rng)
    print(f"Stores: {len(stores)}, Products: {len(products)}")

    price_history = make_price_history(products, dates, rng)
    promotions = make_promotions(products, dates, rng)
    list_price, shelf_price, promo_flag = daily_price_matrix(products, price_history, promotions, dates)

    master_dir = os.path.join(args.out, "master")
    os.makedirs(master_dir, exist_ok=True)
    stores.drop(columns=["_size_factor"]).to_csv(os.path.join(master_dir, "stores.csv"), index=False)
    products.drop(columns=[c for c in products.columns if c.startswith("_")]) \
        .to_csv(os.path.join(master_dir, "products.csv"), index=False)
    price_history.to_csv(os.path.join(master_dir, "price_history.csv"), index=False)
    promotions.to_csv(os.path.join(master_dir, "promotions.csv"), index=False)
    print(f"Master data written. Price history rows: {len(price_history):,}, promos: {len(promotions):,}")

    print("Generating sales (monthly partitions)...")
    total = generate_sales(stores, products, dates, list_price, shelf_price, promo_flag,
                           rng, os.path.join(args.out, "sales"))
    print(f"Total sales rows: {total:,}")

    print("Generating competitor feed...")
    generate_competitor_feed(products, dates, list_price, rng, os.path.join(args.out, "competitor"))
    print("Done.")


if __name__ == "__main__":
    main()
