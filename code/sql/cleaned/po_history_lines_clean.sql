create or replace view po_history_lines_clean as 
SELECT 
-- PO IDs
    POLNF_KEY,
    POLN_POHD_KEY,
    POLN_PO_NO,
    POLN_SUB_PO_NO,
    POLN_SEQ_NO,
    POLN_PARENT_SEQ_NO,
    TRIM(POLN_VENDOR_NAME) AS POLN_VENDOR_NAME,

-- Item Info
    TRIM(POLN_ITEM_NO) AS POLN_ITEM_NO,
    SUBSTRING(POLN_ITEM_NO, 1, 2) AS POLN_ITEM_CLASS_NO,
    TRIM(SUBSTRING_INDEX(POLN_ITEM_DESC, ' ', 1)) AS POLN_ITEM_CLASS_NAME,
    TRIM(POLN_ITEM_DESC) AS POLN_ITEM_DESC,
    SUBSTRING_INDEX(SUBSTRING_INDEX(TRIM(POLN_ITEM_DESC), ' ', 2),' ',-1) AS POLN_ITEM_GAUGE,
    POLN_VMI_TAG_NO,

-- Date Info
    DATE_FORMAT(CAST(POLN_DELIV_DATE AS DATE), '%Y-%m-%d') AS POLN_DELIV_DATE,

-- Quantity Info
    CAST(POLN_ORDER_QTY AS UNSIGNED) AS POLN_ORDER_QTY,

-- Financial Info
    CAST(POLN_ITEM_PRICE AS DECIMAL(10,2)) AS POLN_ITEM_PRICE,
    CAST(POLN_RCVD_PRICE AS DECIMAL(10,2)) AS POLN_RCVD_PRICE,
    CAST(POLN_EXT_AMT AS DECIMAL(10,2)) AS POLN_TOTAL_COST,

-- Other Info
    CAST(POLN_ITEM_CONV_FACTOR AS UNSIGNED) AS POLN_CONV_FACTOR

from po_history_lines

where 

-- Class Filter
    substring(poln_item_no, 1, 2) between 12 and 67

-- Quantity Filter
    and poln_order_qty > 0

-- Date Filter
  and poln_deliv_date > '2014-01-01'

-- Item Number Filter
    and trim(POLN_ITEM_NO) NOT IN ('1', 'X', 'C', 'F', 'TAG', 'SPEC', 
                                   'COIL PROCESS', 'WIRE16', 'WIRE14', 'WIRE14HRPO')

-- VMI Tag Null Filter
    and POLN_VMI_TAG_NO IS NOT NULL

-- Item Type Filter
    and STRIP_DIGITS(TRIM(POLN_ITEM_NO)) NOT IN ('DROP', 'SHEET')

-- Description Filter
    and SUBSTRING_INDEX(TRIM(POLN_ITEM_DESC), ' ', 1) not in 
        ('**', 'COATED', 'MISCELLANEOUS', 'BOND', 'PTD', 'ALMZ', 
        'PTDCR', 'GVLM', 'GLVM', 'GLVM', 'CRFH', 'PTDGVLM', 'EG', 
        'EMBGALV', 'PTDGALV', 'POTLDRY', 'GALVEMB', 'PTDHR', '2', 
        'HRPTD', 'SECONDARY', 'PAINTED', 'PTDGVLMGV', 'PTDGALV/GVLM',
        'HRFP', 'POTP', 'GF', 'FLPL')
;




-- Full pl
select * from po_history_lines_clean;