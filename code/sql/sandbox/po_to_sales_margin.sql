CREATE OR REPLACE VIEW po_to_sales_margin AS
SELECT 
    -- Linking Identifier
    pl.poln_vmi_tag_no,

    -- Buy Information (Purchase Orders)
    pl.poln_vendor_name,
    pl.poln_item_class_no,
    pl.poln_item_no,
    pl.poln_item_class_name,
    pl.poln_item_desc,
    pl.poln_date_goods_recd,
    pl.poln_deliv_date,
    pl.poln_order_qty,
    pl.poln_item_cost,

    -- Sell Information (Customer Orders)
    oh.ordh_cust_no,
    ol.ordl_item_class_no,
    ol.ordl_item_no,
    ol.ordl_item_class_name,
    ol.ordl_item_desc,
    DATE_FORMAT(oh.ordh_ord_date, '%Y-%m-%d') AS  ORDH_ORD_DATE,
    ol.ordl_order_qty,
    ol.ordl_item_cost,
    ol.ordl_item_rev,

    -- Calculated Unit Costs & Margins
    (ol.ordl_item_cost / pl.poln_order_qty) AS ITEM_UNIT_COST,
    (ol.ordl_item_cost - pl.poln_item_cost) AS ITEM_PROCESSING_COST,
    ((ol.ordl_item_cost * ol.ordl_order_qty) / pl.poln_order_qty) AS ITEM_COGS,
    (ol.ordl_item_rev - ((ol.ordl_item_cost * ol.ordl_order_qty) / pl.poln_order_qty)) AS ITEM_GROSS_PROFIT,
    ((ol.ordl_item_rev - ((ol.ordl_item_cost * ol.ordl_order_qty) / pl.poln_order_qty)) / ol.ordl_item_rev) AS ITEM_GROSS_MARGIN,
    ol.ordl_total_profit

FROM order_history_lines_clean ol
LEFT JOIN order_history_hdrs_clean oh
    ON ol.ordlf_ordh_key = oh.ordhf_key
LEFT JOIN po_history_lines_clean pl
    ON ol.ordl_vmit_tag_no = pl.poln_vmi_tag_no
WHERE pl.poln_date_goods_recd IS NOT NULL
ORDER BY pl.poln_date_goods_recd DESC;



select * from po_to_sales_margin;

-- Full po lines
select * from po_history_lines_clean;

-- Full ord lines
select * from order_history_lines_clean;


select ordl_vmit_tag_no from order_history_lines_clean
where ordl_vmit_tag_no in (select poln_vmi_tag_no from po_history_lines_clean);


select * from vmitags_clean where vmit_from_vmi_tag_no <> vmit_org_vmi_tag_no;