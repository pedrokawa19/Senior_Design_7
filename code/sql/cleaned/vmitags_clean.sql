create or replace view vmitags_clean as
select
    -- Item numbers and order references
    vmitf_key,
    cast(substring(vmit_item_no, 1, 2) as unsigned) as vmit_item_class_no,
    nullif(trim(vmit_item_no), '') as vmit_item_no,
    STRIP_DIGITS(TRIM(vmit_item_no)) AS VMIT_ITEM_NO_SUFF,
    nullif(trim(vmit_tag_desc), '') as vmit_tag_desc,
    SUBSTRING_INDEX(TRIM(vmit_tag_desc), ' ', 1) AS VMIT_ITEM_CLASS_NAME,
    vmit_from_vmi_tag_no as vmit_parent_tag_no,
    vmit_org_vmi_tag_no as vmit_org_tag_no,
    cast(vmit_poln_po_num as unsigned) as vmit_poln_po_no,
    cast(vmit_poln_sub_po_no as unsigned) as vmit_poln_sub_po_no,
    cast(vmit_poln_seq_no as unsigned) as vmit_poln_seq_no,
    cast(vmit_sales_order as unsigned) as vmit_ordl_order_no,

    -- Dates
    nullif(cast(vmit_po_date as date), date '1900-01-01') as vmit_po_date,
    nullif(cast(vmit_po_rcvd_date as date), date '1900-01-01') as vmit_po_rcvd_date,
    nullif(cast(vmit_tag_po_date as date), date '1900-01-01') as vmit_tag_po_date,

    -- Financial and quantity fields
    cast(vmit_qty as decimal(14, 2)) as vmit_qty,
    cast(vmit_cost as decimal(12, 3)) as vmit_cost,
    cast(vmit_processor_wgt as decimal(14, 2)) as vmit_processor_wgt,
    cast(vmit_qty_status as unsigned) as vmit_qty_status,

    -- Item information
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

where 
    vmit_item_no not in (0,1)

-- Quantity Filter
    and vmit_qty > 0

-- Date Filter
    and vmit_po_date >= '2014-01-01'

-- Status Filter
    and vmit_qty_status not in (9)

-- Class Filter
    and cast(substring(vmit_item_no, 1, 2) as unsigned) between 12 and 67

-- Type Filter
    and STRIP_DIGITS(TRIM(vmit_item_no)) not in ('X', 'TOLL', 'TUBE', 'PLATE', 
                                                'DECK', 'BEAM', 'FLPLATE', 'EQUIP', 
                                                'CHAN', 'REJECT', 'SLIT', 'FP', 'SHEET', 
                                                'PIPE', 'M', 'T', 'ANG', 'BAR', 'DROP')

-- Description Filter
    and SUBSTRING_INDEX(TRIM(vmit_tag_desc), ' ', 1) not in ('BOND', '20', '24', '5', '4', 
                                                            'PTDGALV', 'PTDGVLM', 'PTD', 'PTDGLVM', 'PTDCR',
                                                            'ALMZ', 'ALZM', 'MISCELLANEOUS', 'GVLM', 'EG', 'GALVEMB', '',
                                                            '.030', '20GA', 'AZ50', '48"', '7GA', '9GALV', 'ADJUSTMENT',
                                                            'CLEAT','G40', 'EmbGALV', '18GA', 'SCRAP', '24GA',
                                                            '____________________________', 'GF', 'PAINTED', '2', 'GV',
                                                            'PL', '36"', 'POTLDRY', 'CRFH', 'HRPD', 'HRPDry', 'POTP',
                                                            'PTDHR', 'FLPL', 'HRP_DRY');


select distinct vmit_item_class_name, count(*) from vmitags_clean
group by vmit_item_class_name order by count(*) desc;


select * from vmitags_clean;
