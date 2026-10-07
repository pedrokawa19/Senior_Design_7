"""Read-only, database-paginated access to the existing inventory view."""

from django.utils import timezone

from .database import get_database_connection

PAGE_SIZE = 50
COLUMNS = (
    ("vmitf_key", "Tag key"),
    ("vmit_item_no", "Item number"),
    ("vmit_tag_desc", "Description"),
    ("vmit_parent_tag_no", "Parent tag"),
    ("vmit_org_tag_no", "Original tag"),
    ("vmit_poln_po_no", "PO number"),
    ("vmit_poln_sub_po_no", "Sub-PO number"),
    ("vmit_poln_seq_no", "PO sequence"),
    ("vmit_po_date", "PO date"),
    ("vmit_qty", "Quantity"),
    ("vmit_piece_cnt", "Piece count"),
    ("vmit_cost", "Cost"),
    ("vmit_qty_status", "Quantity status"),
    ("vmit_order_cust", "Order customer"),
    ("vmit_bin_loc", "Bin location"),
    ("vmit_defect", "Defect"),
    ("vmit_hardness", "Hardness"),
    ("vmit_grade", "Grade"),
    ("vmit_surface", "Surface"),
    ("vmit_coating_wgt", "Coating weight"),
    ("vmit_yield", "Yield"),
    ("vmit_tensile", "Tensile"),
    ("vmit_elongation", "Elongation"),
)


class InvalidInventorySchema(ValueError):
    """The live view does not match the supplied inventory query."""


def get_inventory(settings, *, page=1, sort_column=None, sort_direction=""):
    if page < 1:
        raise ValueError("Choose a positive page number.")
    if ((sort_column is None) != (not sort_direction)
            or sort_direction not in ("", "asc", "desc")
            or (sort_column is not None and not 0 <= sort_column < len(COLUMNS))):
        raise ValueError("Choose a valid inventory sort column and direction.")
    order = "vmit_po_date DESC, vmitf_key DESC"
    if sort_column is not None:
        column = COLUMNS[sort_column][0]
        # Identifiers and direction come only from the validated allowlist.
        order = f"{column} IS NULL, {column} {sort_direction.upper()}, vmitf_key DESC"

    connection = get_database_connection(settings)
    try:
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM current_inventory")
            total = cursor.fetchone()[0]
            page_count = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
            page = min(page, page_count)
            cursor.execute(
                f"SELECT * FROM current_inventory ORDER BY {order} LIMIT %s OFFSET %s",
                (PAGE_SIZE, (page - 1) * PAGE_SIZE),
            )
            rows = cursor.fetchall()
            columns = [column[0] for column in cursor.description]
            if [column.lower() for column in columns] != [column[0] for column in COLUMNS]:
                raise InvalidInventorySchema(
                    "The current_inventory view does not match the expected columns. "
                    "Ask the database administrator to verify its definition."
                )
        finally:
            cursor.close()
    finally:
        connection.close()

    return {
        "columns": columns,
        "column_labels": [label for _, label in COLUMNS],
        "rows": rows,
        "row_count": len(rows),
        "total_rows": total,
        "page": page,
        "page_count": page_count,
        "page_size": PAGE_SIZE,
        "refreshed_at": timezone.now().isoformat(),
        "expires_at": None,
    }
