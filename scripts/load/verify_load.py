"""Verify database load was successful"""
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

connection_string = (
    f"{os.getenv('DB_TYPE')}://{os.getenv('DB_USER')}:"
    f"{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:"
    f"{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

engine = create_engine(connection_string)

queries = {
    'Total Households': "SELECT COUNT(*) FROM Org X.dim_household",
    'Control Group': "SELECT COUNT(*) FROM Org X.dim_household WHERE control_group = true",
    'Products': "SELECT COUNT(*) FROM Org X.dim_product",
    'Adoptions': "SELECT COUNT(*) FROM Org X.fact_adoptions",
    'Counties': "SELECT COUNT(*) FROM Org X.dim_geography"
}

print("\n=== DATABASE VERIFICATION ===\n")
for name, query in queries.items():
    result = pd.read_sql(query, engine).iloc[0, 0]
    print(f"{name}: {result:,}")

print("\n=== ADOPTION SUMMARY BY COUNTY ===\n")
summary = pd.read_sql("""
    SELECT g.county, COUNT(*) as adoptions
    FROM Org X.fact_adoptions f
    JOIN Org X.dim_geography g ON f.geography_key = g.geography_key
    GROUP BY g.county
    ORDER BY adoptions DESC
    LIMIT 5
""", engine)
print(summary)
