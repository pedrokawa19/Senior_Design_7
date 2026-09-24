# Imports
import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Searches for .env
load_dotenv()

# Get database information
user = os.getenv("DB_USER")
password = os.getenv("DB_PASS")
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
database = os.getenv("DB_DATABASE")

# Create SQL engine
engine = create_engine(
    f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}",
    connect_args={"connection_timeout": 5}
)

def run(query):
    return pd.read_sql(query, con=engine)


query = """
select 
item_class_name,
    sum(item_ytd_profit) as ytd_profit_per_class,
    round(sum(item_ytd_profit) / (
        select sum(item_ytd_profit)
        from items_clean
    ) * 100, 2) as profit_share
 from items_clean
group by item_class_name
order by ytd_profit_per_class desc
limit 5;
"""

print(run(query))