import os
import pandas as pd
import openpyxl


pd.set_option("display.max_columns", None)
ROOT_DIR = "../"
EXTERNAL_DIR = "../data/external/"


def clean_bank_rate():
    df = pd.read_csv(EXTERNAL_DIR + "bank_rate.csv")
    return df


def clean_mortgage_rates():
    df = pd.read_csv(EXTERNAL_DIR + "mortgage_rates.csv")
    df = df.rename(columns={
        "Monthly interest rate of UK monetary financial institutions (excl. Central Bank) sterling 2 year (95% LTV) fixed rate mortgage to households (in percent) not seasonally adjusted              [a] [b] [c]             IUM2WTL": "2 year 95% LTV",
        "Monthly interest rate of UK monetary financial institutions (excl. Central Bank) sterling 2 year (90% LTV) fixed rate mortgage to households (in percent) not seasonally adjusted              [d] [e] [b] [c]             IUMB482": "2 year 90% LTV",
        "Monthly interest rate of UK monetary financial institutions (excl. Central Bank) sterling 2 year (75% LTV) fixed rate mortgage to households (in percent) not seasonally adjusted              [a] [d] [b] [c]             IUMBV34": "2 year 75% LTV",
        "Monthly interest rate of UK monetary financial institutions (excl. Central Bank) sterling 2 year (60% LTV) fixed rate mortgage to households (in percent) not seasonally adjusted              [b] [c]             IUMZICQ": "2 year 60% LTV",
        "Monthly interest rate of UK monetary financial institutions (excl. Central Bank) sterling 2 year (85% LTV) fixed rate mortgage to households (in percent) not seasonally adjusted              [b] [c]             IUMZICR": "2 year 85% LTV"
    })
    return df


def clean_regional_employment():
    df = pd.read_csv(EXTERNAL_DIR + "regional_employment_rate.csv")
    df = df.dropna()
    return df


def clean_inflation_rate():
    def columns(df):
        cols = [col for col in df.columns]
        cols[0] = "year"
        cols[1] = "month"
        cols = [col.lower() for col in cols]
        return cols

    def clean_inflation_csv(file, year, cpi_col, ind):
        df = pd.read_csv(EXTERNAL_DIR + file, skiprows=3)
        df.columns = columns(df)
        for index, row in df.iterrows():
            if index < ind:
                df.at[index, "year"] = year
        df = df.dropna()
        cols_to_keep = ["year", "month", cpi_col]
        df = df[cols_to_keep]
        df = df.rename(columns={cpi_col: "cpi_rate"})
        return df

    df1 = clean_inflation_csv("2022-23_inflation_rate.csv", 2022, "cpi 12- \nmonth rate", 12)
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

    return df


def clean_regional_gdp():
    df = pd.read_excel(
        io=EXTERNAL_DIR + "regional_gdp.xlsx", sheet_name=3, engine="openpyxl", skiprows=1)

    cols_to_keep = ["LA name", "2022"]
    df = df[cols_to_keep]
    # print(df[df["LA name"] == "Blackpool"]["2022"])
    return df


def run_clean():
    bank_rate = clean_bank_rate()
    mortgage_rate = clean_mortgage_rates()
    regional_employment = clean_regional_employment()
    inflation_rate = clean_inflation_rate()
    regional_gdp = clean_regional_gdp()

    return bank_rate, mortgage_rate, regional_employment, inflation_rate,\
        regional_gdp


if __name__ == "__main__":
    run_clean()
