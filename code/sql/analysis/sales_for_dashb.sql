select 
ordlf_key,
ordlf_ordh_key,
ordl_item_no,
ordl_item_desc,
ordl_item_class,
date_format(oh.ordh_ord_date, '%Y-%m-%d') as ordh_ord_date,
oh.ordh_cust_no as ordh_cust_no,
ordl_order_qty,
ordl_item_rev,
ordl_item_cost,
ordl_total_profit
from order_history_lines_clean ol
left join order_history_hdrs_clean oh
on ol.ordlf_ordh_key = oh.ordhf_key
order by ordh_ord_date desc
limit 2000;