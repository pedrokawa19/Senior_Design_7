-- Corresponding dashboard code: web-django/dashboard/services/history.py:53
-- Corresponding dashboard caller: web-django/dashboard/views/api.py:229
-- Last updated: 2026-10-06

select 
-- IDs
ordlf_key,
ordl_vmit_tag_no,

-- Customer
oh.ordh_cust_no as ORDH_CUST_NO,

-- Item Details
ordl_item_no,
ordl_item_desc,

-- Date
oh.ordh_ord_date as ORDH_ORD_DATE,

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
order by oh.ordh_ord_date desc, ol.ordlf_key desc;