import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, text


# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DATA_PATH = BASE_DIR / "data" / "raw" / "expenses_raw.csv"
PROCESSED_DATA_PATH = (
    BASE_DIR / "data" / "processed" / "expenses_clean.csv"
)

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

EXPECTED_COLUMNS = {
    "date",
    "transaction_id",
    "amount",
    "category",
    "merchant",
    "payment_mode",
    "description",
}

# Extract and transform

def extract_data():
    """Load raw transaction data from CSV."""

    df = pd.read_csv(RAW_DATA_PATH)

    print(f"Loaded {len(df)} transactions.")

    return df


def validate_schema(df):
    """Validate that required columns exist in the dataset."""

    missing_columns = EXPECTED_COLUMNS - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    print("Schema validation passed.")

def remove_duplicates(df):
    """Remove exact duplicate transaction records."""

    initial_rows = len(df)

    df = df.drop_duplicates().copy()

    removed_rows = initial_rows - len(df)

    print(f"Removed {removed_rows} duplicate transactions.")

    return df

def handle_missing_values(df):
    """Handle missing values in transaction data."""

    missing_payment_modes = df["payment_mode"].isna().sum()

    df["payment_mode"] = df["payment_mode"].fillna("Unknown")

    print(
        f"Filled {missing_payment_modes} missing payment modes with 'Unknown'."
    )

    return df

def convert_data_types(df):
    """Convert columns to appropriate data types."""

    df["date"] = pd.to_datetime(df["date"])

    print("Converted date column to datetime.")

    return df

def standardize_text(df):
    """Standardize text columns."""

    text_columns = [
        "category",
        "merchant",
        "payment_mode",
        "description",
    ]

    for column in text_columns:
        df[column] = df[column].str.strip()

    print("Standardized text columns.")

    return df

# Feature engineering 

def create_date_features(df):
    """Create date-based analytical features."""

    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month_name()
    df["month_number"] = df["date"].dt.month
    df["day"] = df["date"].dt.day
    df["weekday"] = df["date"].dt.day_name()
    df["is_weekend"] = df["date"].dt.dayofweek >= 5

    print("Created date-based features.")

    return df

def create_spending_tiers(df):
    """Categorize transactions into spending tiers."""

    bins = [0, 200, 500, 1000, float("inf")]

    labels = [
        "Low",
        "Medium",
        "High",
        "Very High",
    ]

    df["spending_tier"] = pd.cut(
        df["amount"],
        bins=bins,
        labels=labels,
        include_lowest=True,
    )

    print("Created spending tiers.")

    return df

def detect_anomalies(df):
    """Flag unusually high transaction amounts using the IQR method."""

    q1 = df["amount"].quantile(0.25)
    q3 = df["amount"].quantile(0.75)

    iqr = q3 - q1
    upper_bound = q3 + (1.5 * iqr)

    df["is_anomaly"] = df["amount"] > upper_bound

    anomaly_count = df["is_anomaly"].sum()

    print(
        f"Flagged {anomaly_count} anomalous transactions "
        f"above ₹{upper_bound:.2f}."
    )

    return df

def save_processed_data(df):
    """Save cleaned and transformed data to CSV."""

    PROCESSED_DATA_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(
        PROCESSED_DATA_PATH,
        index=False,
    )

    print(
        f"Saved {len(df)} processed transactions "
        f"to {PROCESSED_DATA_PATH}."
    )

# Load

def create_database_engine():
    """Create a connection engine for the MySQL database."""

    database_url = URL.create(
        drivername="mysql+mysqlconnector",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        database=DB_NAME,
    )

    return create_engine(database_url)


def load_to_database(df):
    """Load processed transaction data into MySQL."""

    engine = create_database_engine()

    df.to_sql(
        "transactions",
        engine,
        if_exists="replace",
        index=False,
    )

    print(
        f"Loaded {len(df)} transactions "
        "into MySQL database."
    )


# Verification

def verify_database():
    """Verify transactions were loaded into MySQL."""

    engine = create_database_engine()

    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT COUNT(*) FROM transactions")
        )

        row_count = result.scalar()

    print(
        f"Database verification passed: "
        f"{row_count} transactions found."
    )

if __name__ == "__main__":
    df = extract_data()

    validate_schema(df)

    df = remove_duplicates(df)

    df = handle_missing_values(df)

    df = convert_data_types(df)

    df = standardize_text(df)

    df = create_date_features(df)

    df = create_spending_tiers(df)

    df = detect_anomalies(df)

    save_processed_data(df)

    load_to_database(df)

    verify_database()
