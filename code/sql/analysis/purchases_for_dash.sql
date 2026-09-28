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