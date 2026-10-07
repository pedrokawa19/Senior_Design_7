-- CREATE OR REPLACE VIEW po_to_sales_margin AS
-- SELECT 
--     -- Linking Identifier
--     pl.poln_vmi_tag_no,

--     -- Buy Information (Purchase Orders)
--     pl.poln_vendor_name,
--     pl.poln_item_class_no,
--     pl.poln_item_no,
--     pl.poln_item_class_name,
--     pl.poln_item_desc,
--     pl.poln_date_goods_recd,
--     pl.poln_deliv_date,
--     pl.poln_order_qty,
--     pl.poln_item_cost,

--     -- Sell Information (Customer Orders)
--     oh.ordh_cust_no,
--     ol.ordl_item_class_no,
--     ol.ordl_item_no,
--     ol.ordl_item_class_name,
--     ol.ordl_item_desc,
--     DATE_FORMAT(oh.ordh_ord_date, '%Y-%m-%d') AS  ORDH_ORD_DATE,
--     ol.ordl_order_qty,
--     ol.ordl_item_cost,
--     ol.ordl_item_rev,

--     -- Calculated Unit Costs & Margins
--     (ol.ordl_item_cost / pl.poln_order_qty) AS ITEM_UNIT_COST,
--     (ol.ordl_item_cost - pl.poln_item_cost) AS ITEM_PROCESSING_COST,
--     ((ol.ordl_item_cost * ol.ordl_order_qty) / pl.poln_order_qty) AS ITEM_COGS,
--     (ol.ordl_item_rev - ((ol.ordl_item_cost * ol.ordl_order_qty) / pl.poln_order_qty)) AS ITEM_GROSS_PROFIT,
--     ((ol.ordl_item_rev - ((ol.ordl_item_cost * ol.ordl_order_qty) / pl.poln_order_qty)) / ol.ordl_item_rev) AS ITEM_GROSS_MARGIN,
--     ol.ordl_total_profit

-- FROM order_history_lines_clean ol
-- LEFT JOIN order_history_hdrs_clean oh
--     ON ol.ordlf_ordh_key = oh.ordhf_key
-- LEFT JOIN po_history_lines_clean pl
--     ON ol.ordl_vmit_tag_no = pl.poln_vmi_tag_no
-- WHERE pl.poln_date_goods_recd IS NOT NULL
-- ORDER BY pl.poln_date_goods_recd DESC;

-- select * from po_to_sales_margin;


-- Full vmitags
select * from vmitags_clean;

-- Full po lines
select * from po_history_lines_clean;

-- Full ord lines
select * from order_history_lines_clean;

-- Full ord head
select * from order_history_hdrs_clean;


-- t.j.po.j.ol.j.oh
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
(v.vmitf_key <> v.vmit_org_tag_no and v.vmit_parent_tag_no = v.vmit_org_tag_no) as vmit_is_dir_child_of_org,
v.vmit_qty_status,

-- Buy Information
pl.polnf_key,
pl.poln_vendor_name,
v.vmit_po_date,
v.vmit_po_rcvd_date,
v.vmit_po_rcvd_date - v.vmit_po_date as vmit_po_lead_time,
v.vmit_qty,
pl.poln_item_price,
pl.poln_rcvd_price,
v.vmit_cost,
pl.poln_total_cost,

-- Sell Information
ol.ordlf_key,
ol.ordl_cust_name,
oh.ordh_ord_date,
ol.ordl_order_qty,
ol.ordl_item_rev,
ol.ordl_item_cost,
ol.ordl_total_rev,
ol.ordl_total_cost,
ol.ordl_total_profit,

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
left join po_history_lines_clean pl
    on v.vmitf_key = pl.poln_vmi_tag_no
left join order_history_lines_clean ol
    on v.vmitf_key = ol.ordl_vmit_tag_no
left join order_history_hdrs_clean oh
    on ol.ordlf_ordh_key = oh.ordhf_key
where v.vmit_po_date > '2024-01-01';



select * from order_history_lines_clean where ORDL_VMIT_TAG_NO is null;