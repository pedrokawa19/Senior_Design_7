
-- Debugging
SHOW FULL PROCESSLIST;
KILL QUERY 170;
EXPLAIN FORMAT=JSON FOR CONNECTION 170;


select 
polnf_key,
poln_item_no,
poln_item_class_no,
poln_item_desc,
poln_item_desc_pref,
poln_date_goods_recd
from po_history_lines_clean
limit 1000;


-- EXPLAIN FORMAT=JSON
SELECT
    -- Item Information
    v.vmitf_key,
    v.vmit_item_class,
    v.vmit_item_no,
    v.vmit_tag_desc,

    -- Buy Dates
    v.vmit_po_date,
    v.vmit_tag_po_date,
    pl.poln_deliv_date,
    pl.poln_date_goods_recd,

    -- Vendor
    pl.poln_vendor_name,

    -- Buy Quantity / Weight
    v.vmit_qty,
    pl.poln_order_qty,

    -- Costs
    v.vmit_cost,
    pl.poln_item_cost,
    ol.ordl_item_cost,
    pl.poln_rcvd_price,
    pl.poln_item_total_cost,
    pl.poln_total_cost,
    ol.ordl_total_cost,

    -- Sell Dates
    oh.ordh_ord_date,
    oh.ordh_inv_date,

    -- Customer
    oh.ordh_cust_no,

    -- Sell Quantity / Weight
    ol.ordl_order_qty,

    -- Revenues
    ol.ordl_item_rev,
    ol.ordl_total_rev,

    -- Profit
    ol.ordl_total_profit

FROM vmitags_clean v

LEFT JOIN po_history_lines_clean pl
    ON v.vmitf_key = pl.poln_vmi_tag_no
    AND v.vmit_poln_po_no = pl.poln_po_no
    AND v.vmit_poln_sub_po_no = pl.poln_sub_po_no
    AND v.vmit_poln_seq_no = pl.poln_seq_no

LEFT JOIN order_history_lines_clean ol
    ON v.vmitf_key = ol.ordl_vmit_tag_no

LEFT JOIN order_history_hdrs_clean oh
    ON ol.ordlf_ordh_key = oh.ordhf_key
limit 20;