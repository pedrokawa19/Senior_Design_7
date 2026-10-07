-- Corresponding dashboard code: web-django/dashboard/services/history.py:26
-- Corresponding dashboard caller: web-django/dashboard/views/api.py:223
-- Last updated: 2026-10-06

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
order by poln_deliv_date desc, polnf_key desc;