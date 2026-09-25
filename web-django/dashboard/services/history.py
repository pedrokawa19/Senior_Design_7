"""Purchase and sales history read from the client's MySQL database.

Write the SQL for each report in the two query constants below. Everything else
is already wired up: opening the connection, running the query, converting the
result, and handing it to the History page.

How the page renders a result:
  - Whatever columns your query selects become the table columns, in order.
  - Your column aliases become the column headings shown to the user.
  - Rows appear in the order your query returns them, so sort in SQL.

Until a query is filled in, the matching page shows a "not written yet" notice
instead of raising an error.
"""

import json

import pandas as pd

from .database import get_database_connection

# Safety net so a missing LIMIT cannot pull an unbounded result into memory.
MAX_ROWS = 200


class HistoryQueryNotConfigured(Exception):
    """Raised when a report's SQL has not been written yet."""

PURCHASE_HISTORY_QUERY = """
select
polnf_key,
poln_vendor_name,
poln_item_no,
poln_item_desc,
poln_order_qty,
poln_item_cost,
poln_item_total_cost,
POLN_TOTAL_COST,
POLN_RCVD_PRICE,
poln_deliv_date,
poln_date_goods_recd
from po_history_lines_clean
order by poln_deliv_date desc
limit 250;
"""

SALES_HISTORY_QUERY = """
select 
ordlf_key,
ordlf_ordh_key,
ordl_item_no,
ordl_item_desc,
ordl_item_class,
date_format(oh.ordh_ord_date, '%Y-%m-%d') as ordh_ord_date,
ordl_order_qty,
ordl_item_rev,
ordl_item_cost,
ordl_total_profit
from order_history_lines_clean ol
left join order_history_hdrs_clean oh
on ol.ordlf_ordh_key = oh.ordhf_key
order by ordh_ord_date desc
limit 2000;
"""


def get_purchase_history(settings):
    """Return the most recent purchase orders as a table payload."""
    return _run_history_query(settings, PURCHASE_HISTORY_QUERY, "purchase history")


def get_sales_history(settings):
    """Return the most recent sales orders as a table payload."""
    return _run_history_query(settings, SALES_HISTORY_QUERY, "sales history")


def _run_history_query(settings, query, report_name):
    if not query.strip():
        raise HistoryQueryNotConfigured(
            f"The {report_name} query has not been written yet. "
            "Add it to dashboard/services/history.py."
        )

    connection = get_database_connection(settings)
    try:
        frame = pd.read_sql(query, con=connection)
    finally:
        connection.close()

    return _as_table(frame)


def _as_table(frame):
    frame = frame.head(MAX_ROWS)
    # to_json handles dates, decimals, and missing values that JsonResponse cannot.
    payload = json.loads(frame.to_json(orient="split", date_format="iso"))
    return {
        "columns": [str(column) for column in payload["columns"]],
        "rows": payload["data"],
        "row_count": len(payload["data"]),
    }
