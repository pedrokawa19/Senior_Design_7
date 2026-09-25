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


# ---------------------------------------------------------------------------
# PURCHASE HISTORY
#
# >>> PUT YOUR SQL FOR THE MOST RECENT PURCHASE ORDERS BETWEEN THE QUOTES <<<
#
# Likely source tables (see code/sql/): po_history_hdrs_clean joined to
# po_history_lines_clean.
#
# Tips:
#   - Sort newest first, for example: order by order_date desc
#   - Include a LIMIT so the page stays fast, for example: limit 100
#   - Alias columns to the heading you want, for example:
#       select po_number as "PO Number", vendor_name as "Vendor"
#
# Example of the shape expected (replace this entirely with your own SQL):
#   select
#       h.po_number      as "PO Number",
#       h.vendor_name    as "Vendor",
#       h.order_date     as "Order Date",
#       l.item_description as "Item",
#       l.weight_lbs     as "Weight (lbs)",
#       l.extended_cost  as "Cost"
#   from po_history_hdrs_clean h
#   join po_history_lines_clean l on l.po_number = h.po_number
#   order by h.order_date desc
#   limit 100;
# ---------------------------------------------------------------------------
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
order by poln_deliv_date desc;
"""


# ---------------------------------------------------------------------------
# SALES HISTORY
#
# >>> PUT YOUR SQL FOR THE MOST RECENT SALES ORDERS BETWEEN THE QUOTES <<<
#
# Likely source tables (see code/sql/): order_history_hdrs_clean joined to
# order_history_lines_clean.
#
# The same tips apply: sort newest first, include a LIMIT, and alias columns
# to the headings you want shown.
# ---------------------------------------------------------------------------
SALES_HISTORY_QUERY = """
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
