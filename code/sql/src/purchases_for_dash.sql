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