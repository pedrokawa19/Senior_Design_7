"""Bounded, filtered history snapshots with per-user caching and pagination."""

import json
from datetime import timedelta

from django.core.cache import cache
from django.utils import timezone
from django.utils.crypto import salted_hmac

import pandas as pd

from .database import get_database_connection

MAX_ROWS = 1000
PAGE_SIZE = 100
CACHE_SECONDS = 3600


class InvalidHistorySort(ValueError):
    """The requested column is not present in this report."""


class HistoryQueryNotConfigured(Exception):
    """Raised when a report's SQL has not been written yet."""

PURCHASE_HISTORY_QUERY = """
select
-- IDs
polnf_key,
poln_vmi_tag_no,

-- Vendor
poln_vendor_name,

-- Item Details
poln_item_no,
poln_item_desc,

-- Date
poln_deliv_date,

-- Quantity and Price
poln_order_qty,
poln_item_price,
poln_total_cost

from po_history_lines_clean
{where}
order by poln_deliv_date desc, polnf_key desc
limit 1000;
"""

SALES_HISTORY_QUERY = """
select 
-- IDs
ordlf_key,
ordl_vmit_tag_no,

-- Customer
oh.ordh_cust_no as ordh_cust_no,

-- Item Details
ordl_item_no,
ordl_item_desc,

-- Date
date_format(oh.ordh_ord_date, '%Y-%m-%d') as ordh_ord_date,

-- Quantity and Price
ordl_order_qty,
ordl_item_rev,
ordl_item_cost,
ordl_total_rev,
ordl_total_cost,
ordl_total_profit

from order_history_lines_clean ol
left join order_history_hdrs_clean oh
on ol.ordlf_ordh_key = oh.ordhf_key
{where}
order by ordh_ord_date desc, ol.ordlf_key desc
limit 1000;
"""


def get_purchase_history(settings, **options):
    return _get_history(settings, "purchases", PURCHASE_HISTORY_QUERY, **options)


def get_sales_history(settings, **options):
    return _get_history(settings, "sales", SALES_HISTORY_QUERY, **options)


def _filtered_query(query, report, filters):
    """Apply filters before LIMIT, binding all user input as SQL parameters."""
    date_column, item_column, description_column, party_column = (
        ("poln_deliv_date", "poln_item_no", "poln_item_desc", "poln_vendor_name")
        if report == "purchases" else
        ("oh.ordh_ord_date", "ol.ordl_item_no", "ol.ordl_item_desc", "oh.ordh_cust_name")
    )
    clauses = []
    params = ["%Y-%m-%d"] if report == "sales" else []
    for name, operator in (("start_date", ">="), ("end_date", "<=")):
        if filters.get(name):
            clauses.append(f"{date_column} {operator} %s")
            params.append(filters[name].isoformat())
    # LOCATE treats %, _ and quotes literally, rather than as LIKE wildcards.
    if filters.get("item"):
        clauses.append(f"(LOCATE(%s, {item_column}) > 0 OR LOCATE(%s, {description_column}) > 0)")
        params.extend([filters["item"], filters["item"]])
    if filters.get("party"):
        clauses.append(f"LOCATE(%s, {party_column}) > 0")
        params.append(filters["party"])
    return query.format(where="WHERE " + " AND ".join(clauses) if clauses else ""), params


def _get_history(settings, report, query, *, user_id, connection_version,
                 filters, page=1, refresh=False, sort_column=None, sort_direction=""):
    column_count = 11 if report == "purchases" else 10
    if sort_column is not None and not 0 <= sort_column < column_count:
        raise InvalidHistorySort("Choose a valid column for this report.")
    if not query.strip():
        raise HistoryQueryNotConfigured("The history query has not been written yet.")
    sql, params = _filtered_query(query, report, filters)
    # HMAC keeps connection secrets out of cache filenames. Version changes on
    # every save, including removing and re-adding identical connection settings.
    identity = json.dumps([user_id, connection_version, settings, report, sql, params],
                          sort_keys=True, default=str)
    key = "history:v1:" + salted_hmac("history-cache", identity, algorithm="sha256").hexdigest()
    table = None if refresh else cache.get(key)
    if table is None:
        table = _run_history_query(settings, sql, params)
        refreshed_at = timezone.now()
        table["refreshed_at"] = refreshed_at.isoformat()
        table["expires_at"] = (refreshed_at + timedelta(seconds=CACHE_SECONDS)).isoformat()
        cache.set(key, table, CACHE_SECONDS)
    total = table["row_count"]
    page_count = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = min(page, page_count)
    start = (page - 1) * PAGE_SIZE
    ordered_rows = _sort_rows(table["rows"], sort_column, sort_direction)
    rows = ordered_rows[start:start + PAGE_SIZE]
    return {**table, "rows": rows, "row_count": len(rows), "total_rows": total,
            "page": page, "page_count": page_count, "page_size": PAGE_SIZE,
            "max_rows": MAX_ROWS, "sort_column": sort_column, "sort_direction": sort_direction}


def _sort_rows(rows, column, direction):
    """Stable sorting of the snapshot; never mutate the cached database order.

    Numeric JSON values sort numerically. Text (including ISO dates) sorts
    case-insensitively. Nulls and empty strings remain last in either direction.
    """
    if column is None:
        return rows
    present = [row for row in rows if row[column] is not None and row[column] != ""]
    missing = [row for row in rows if row[column] is None or row[column] == ""]

    def key(row):
        value = row[column]
        return (0, value) if isinstance(value, (int, float)) else (1, str(value).casefold())

    return sorted(present, key=key, reverse=direction == "desc") + missing


def _run_history_query(settings, query, params):
    connection = get_database_connection(settings)
    try:
        frame = pd.read_sql(query, con=connection, params=params)
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
