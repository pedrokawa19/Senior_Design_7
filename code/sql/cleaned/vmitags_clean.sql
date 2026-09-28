create or replace view vmitags_clean as
select
    -- Item numbers and order references
    vmitf_key,
    cast(substring(vmit_item_no, 1, 2) as unsigned) as vmit_item_class,
    nullif(trim(vmit_item_no), '') as vmit_item_no,
    cast(vmit_from_vmi_tag_no as unsigned) as vmit_from_vmi_tag_no,
    cast(vmit_org_vmi_tag_no as unsigned) as vmit_org_vmi_tag_no,
    cast(vmit_poln_po_num as unsigned) as vmit_poln_po_no,
    cast(vmit_poln_sub_po_no as unsigned) as vmit_poln_sub_po_no,
    cast(vmit_poln_seq_no as unsigned) as vmit_poln_seq_no,
    cast(vmit_sales_order as unsigned) as vmit_sales_order,

    -- Dates
    nullif(cast(vmit_po_date as date), date '1900-01-01') as vmit_po_date,
    nullif(cast(vmit_tag_po_date as date), date '1900-01-01') as vmit_tag_po_date,

    -- Financial and quantity fields
    cast(vmit_qty as decimal(14, 2)) as vmit_qty,
    cast(vmit_cost as decimal(12, 3)) as vmit_cost,
    cast(vmit_processor_wgt as decimal(14, 2)) as vmit_processor_wgt,
    cast(vmit_qty_status as unsigned) as vmit_qty_status,

    -- Item information
    nullif(trim(vmit_tag_desc), '') as vmit_tag_desc,
    nullif(trim(vmit_order_cust), '') as vmit_order_cust,
    nullif(trim(vmit_bin_loc), '') as vmit_bin_loc,
    nullif(trim(vmit_processor_tag_nbr), '') as vmit_processor_tag_nbr,
    nullif(trim(vmit_mill_tag_nbr), '') as vmit_mill_tag_nbr,
    nullif(trim(vmit_hardness), '') as vmit_hardness,
    nullif(trim(vmit_grade), '') as vmit_grade,
    nullif(trim(vmit_surface), '') as vmit_surface,
    cast(vmit_coating_wgt as decimal(10, 4)) as vmit_coating_wgt,
    cast(vmit_piece_cnt as unsigned) as vmit_piece_cnt,
    cast(vmit_yield as decimal(10, 3)) as vmit_yield,
    cast(vmit_tensile as decimal(10, 3)) as vmit_tensile,
    cast(vmit_elongation as decimal(10, 3)) as vmit_elongation,
    nullif(trim(vmit_defect), '') as vmit_defect
from vmi_tags
where vmit_item_no not in (0,1);


select * from vmitags_clean order by vmit_po_date asc limit 10;


-- select max(vmit_po_date) as max_po_date FROM vmitags_clean;
-- select min(vmit_po_date) as min_po_date FROM vmitags_clean;
