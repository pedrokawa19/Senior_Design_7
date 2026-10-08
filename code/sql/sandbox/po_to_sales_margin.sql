CREATE OR REPLACE VIEW po_to_sales_margin AS

select

-- Item IDs
    v.vmitf_key,
    v.vmit_item_class_no,
    v.vmit_item_class_name,
    v.vmit_item_no,
    v.vmit_tag_desc,
    v.vmit_parent_tag_no,
    v.vmit_org_tag_no,
    v.vmitf_key = v.vmit_org_tag_no as vmit_is_org,
    v.vmitf_key <> v.vmit_org_tag_no as vmit_is_child,
    (
        v.vmitf_key <> v.vmit_org_tag_no
        and v.vmit_parent_tag_no = v.vmit_org_tag_no
    ) as vmit_is_dir_child_of_org,
    v.vmit_qty_status,

-- Buy Information
    pl.polnf_key,
    pl.poln_vendor_name,
    v.vmit_po_date,
    v.vmit_po_rcvd_date,
    v.vmit_po_rcvd_date - v.vmit_po_date as vmit_po_lead_time,
    v.vmit_qty,
    pl.poln_item_price,
    v.vmit_cost,
    v.vmit_cost - pl.poln_item_price as processing_cost,
    pl.poln_total_cost,

-- Sell Information
    ol.ordlf_key,
    ol.ordl_cust_name,
    oh.ordh_ord_date,
    ol.ordl_order_qty,
    ol.ordl_item_rev,
    ol.ordl_total_rev,
    ol.ordl_total_cost,
    ol.ordl_total_profit,

-- Financial Information
    (v.vmit_cost / v.vmit_qty) AS ITEM_UNIT_COST,
    ((v.vmit_cost * ol.ordl_order_qty) / v.vmit_qty) AS ITEM_COGS,
    (
        ol.ordl_item_rev - ((v.vmit_cost * ol.ordl_order_qty) / v.vmit_qty)
    ) AS ITEM_GROSS_PROFIT,
    (
        (
            ol.ordl_item_rev - ((v.vmit_cost * ol.ordl_order_qty) / v.vmit_qty)
        ) / ol.ordl_item_rev
    ) AS ITEM_GROSS_MARGIN,

-- Item Details
    v.vmit_bin_loc,
    v.vmit_hardness,
    v.vmit_grade,
    v.vmit_surface,
    v.vmit_coating_wgt,
    v.vmit_piece_cnt,
    v.vmit_yield,
    v.vmit_tensile,
    v.vmit_elongation,
    v.vmit_defect
from vmitags_clean v
    left join po_history_lines_clean pl on v.vmitf_key = pl.poln_vmi_tag_no
    left join order_history_lines_clean ol on v.vmitf_key = ol.ordl_vmit_tag_no
    left join order_history_hdrs_clean oh on ol.ordlf_ordh_key = oh.ordhf_key
;

select * from po_to_sales_margin;


-- Full vmitags
select * from vmitags_clean;
-- Full po lines
select * from po_history_lines_clean;
-- Full ord lines
select * from order_history_lines_clean;
-- Full ord head
select * from order_history_hdrs_clean;