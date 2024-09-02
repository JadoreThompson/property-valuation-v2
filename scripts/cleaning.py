import numpy as np
import pandas as pd
from app import ROOT_DIR
import os

pd.set_option("display.max_columns", None)

EXTERNAL_DIR = os.path.join(ROOT_DIR, "data", "external")


def clean_bank_rate():
    df = pd.read_csv(os.path.join(EXTERNAL_DIR, "bank_rate.csv"))
    df.columns = df.columns.str.lower()
    df = df.drop_duplicates()
    return df


def clean_mortgage_rates():
    df = pd.read_csv(os.path.join(EXTERNAL_DIR, "mortgage_rates.csv"))

    df = df.rename(columns={
        "Monthly interest rate of UK monetary financial institutions (excl. Central Bank) sterling 2 year (95% LTV) fixed rate mortgage to households (in percent) not seasonally adjusted              [a] [b] [c]             IUM2WTL": "2 year 95% LTV",
        "Monthly interest rate of UK monetary financial institutions (excl. Central Bank) sterling 2 year (90% LTV) fixed rate mortgage to households (in percent) not seasonally adjusted              [d] [e] [b] [c]             IUMB482": "2 year 90% LTV",
        "Monthly interest rate of UK monetary financial institutions (excl. Central Bank) sterling 2 year (75% LTV) fixed rate mortgage to households (in percent) not seasonally adjusted              [a] [d] [b] [c]             IUMBV34": "2 year 75% LTV",
        "Monthly interest rate of UK monetary financial institutions (excl. Central Bank) sterling 2 year (60% LTV) fixed rate mortgage to households (in percent) not seasonally adjusted              [b] [c]             IUMZICQ": "2 year 60% LTV",
        "Monthly interest rate of UK monetary financial institutions (excl. Central Bank) sterling 2 year (85% LTV) fixed rate mortgage to households (in percent) not seasonally adjusted              [b] [c]             IUMZICR": "2 year 85% LTV"
    })

    df["Date"] = pd.to_datetime(df["Date"], format="%d %b %y")
    df["year"] = df["Date"].dt.year
    df["month"] = df["Date"].dt.month
    df["day"] = df["Date"].dt.day

    month_mapping = {
        1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
        7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
    }
    df["month"] = df["month"].map(month_mapping)
    df = df.sort_values(["year", "month", "day"])
    df = df.drop_duplicates()
    return df


def clean_regional_employment():
    df = pd.read_csv(os.path.join(EXTERNAL_DIR, "regional_employment_rate.csv"))

    df = df.dropna()

    df_melted = df.melt(id_vars=['Area name'],
                        var_name='Year',
                        value_name='Value')
    df_melted = df_melted.sort_values(['Area name', 'Year'])
    df_melted = df_melted.reset_index(drop=True)
    df_melted = df_melted.drop_duplicates()

    return df_melted


def clean_inflation_rate():
    def columns(df):
        cols = [col for col in df.columns]
        cols[0] = "year"
        cols[1] = "month"
        cols = [col.lower() for col in cols]
        return cols

    def clean_inflation_csv(file, year, cpi_col, ind):
        df = pd.read_csv(os.path.join(EXTERNAL_DIR, file), skiprows=3)
        df.columns = columns(df)
        for index, row in df.iterrows():
            if index < ind:
                df.at[index, "year"] = year
        df = df.dropna()
        cols_to_keep = ["year", "month", cpi_col]
        df = df[cols_to_keep]
        df = df.rename(columns={cpi_col: "cpi_rate"})

        df = df.drop_duplicates()
        return df

    df1 = clean_inflation_csv("2022-23_inflation_rate.csv", 2022, "cpi 12- \r\nmonth rate", 12)
    df2 = clean_inflation_csv("2023-24_inflation_rate.csv", 2023, "cpi 12- \nmonth \nrate (%)", 6)
    df = pd.concat([df1, df2], axis=0, ignore_index=True)

    month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    df["month"] = pd.Categorical(df["month"], categories=month_order, ordered=True)
    df = df.sort_values(by=["year", "month"])

    years = df['year'].unique()
    all_months = pd.DataFrame([(year, month) for year in years for month in month_order],
                              columns=['year', 'month'])

    df = pd.merge(all_months, df, on=['year', 'month'], how='left')

    df["month"] = pd.Categorical(df["month"], categories=month_order, ordered=True)
    df = df.sort_values(by=['year', 'month'])

    df['cpi_rate'] = df.groupby('year')['cpi_rate'].fillna(method='ffill')
    # df['cpi_rate'] = df.groupby('year')['cpi_rate'].fillna(method='bfill')

    df["month"] = pd.Categorical(df["month"], categories=month_order, ordered=True)
    df = df.sort_values(by=["year", "month"])

    df = df.drop_duplicates()
    return df


def clean_regional_gdp():
    df = pd.read_excel(
        io=os.path.join(EXTERNAL_DIR, "regional_gdp.xlsx"), sheet_name=3, engine="openpyxl", skiprows=1)

    cols_to_keep = ["LA name", "2022"]
    df = df[cols_to_keep]
    df = df.rename(columns={"LA name": "borough"})

    df = df.drop_duplicates()

    return df


def clean_lr_data():
    def make_full_address(row):
        full_address = f"{row['saon']+',' if pd.notna(row['saon']) and row['saon'] != '' else ''} {row['paon']}, {row['street']}, {row["town"]}, {row["county"]} {row["postcode"]}".strip()
        full_address = full_address.title()
        parts = full_address.split()
        parts[-1] = parts[1][0] + parts[-1][-2:].upper()
        return " ".join(parts)

    df = pd.read_csv(os.path.join(EXTERNAL_DIR, "last_2y.csv"))
    cols = [col for col in df.columns][-16:]
    df = df.drop(cols, axis=1)
    df = df.drop("unique_id", axis=1)

    df = df.rename(columns={
        "deed_date": "sold_date"
    })

    df["sold_date"] = pd.to_datetime(df["sold_date"], format="%Y-%m-%d")
    df["year"] = df["sold_date"].dt.year
    df["month"] = df["sold_date"].dt.month
    df["day"] = df["sold_date"].dt.day

    df["estate_type"] = df["estate_type"].map({"L": "Lease", "F": "Freehold"})
    df["property_type"] = df["property_type"].map({"F": "Flat/Maisonette",
                                                   "T": "Terraced",
                                                   "O": "Other",
                                                   "S": "Semi-detached",
                                                   "D": "Detached"
                                                   })

    df["address"] = df.apply(lambda row: f"{row['saon'] if pd.notna(row['saon']) and row['saon'] != '' else ''} {row['paon']} {row['street']}".strip(),axis=1)
    df["full_address"] = df.apply(lambda row: make_full_address(row), axis=1)

    df = df[df["year"] >= 2022]
    df = df.drop_duplicates(subset=["address"])
    return df


def run_clean():
    bank_rate = clean_bank_rate()
    mortgage_rate = clean_mortgage_rates()
    regional_employment = clean_regional_employment()
    inflation_rate = clean_inflation_rate()
    regional_gdp = clean_regional_gdp()
    data_2y = clean_lr_data()

    return bank_rate, mortgage_rate, regional_employment, inflation_rate,\
        regional_gdp, data_2y


if __name__ == "__main__":
    run_clean()
