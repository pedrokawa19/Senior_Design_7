"""Year-to-date profit by item class, read from the client's MySQL database."""

import pandas as pd

from .database import get_database_connection

TOP_FIVE_QUERY = """
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


def get_profitable_products(settings):
    connection = get_database_connection(settings)
    try:
        products = pd.read_sql(TOP_FIVE_QUERY, con=connection)
    finally:
        connection.close()

    return [
        {
            "rank": index + 1,
            "product": row["item_class_name"],
            "ytd_profit": float(row["ytd_profit_per_class"]),
            "profit_share": float(row["profit_share"]),
        }
        for index, row in products.iterrows()
    ]
