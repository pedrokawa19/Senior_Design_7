create or replace view po_history_lines_clean as 
SELECT 
-- PO IDs
    TRIM(POLNF_KEY) AS POLNF_KEY,
    CAST(POLN_POHD_KEY AS UNSIGNED) AS POLN_POHD_KEY,
    CAST(POLN_PO_NO AS UNSIGNED) AS POLN_PO_NO,
    CAST(POLN_SUB_PO_NO AS UNSIGNED) AS POLN_SUB_PO_NO,
    CAST(POLN_SEQ_NO AS UNSIGNED) AS POLN_SEQ_NO,
    CAST(POLN_PARENT_SEQ_NO AS UNSIGNED) AS POLN_PARENT_SEQ_NO,
    TRIM(POLN_VENDOR_NAME) AS POLN_VENDOR_NAME,

-- Item Info
    TRIM(POLN_ITEM_NO) AS POLN_ITEM_NO,
    SUBSTRING(POLN_ITEM_NO, 1, 2) AS POLN_ITEM_CLASS_NO,
    TRIM(SUBSTRING_INDEX(POLN_ITEM_DESC, ' ', 1)) AS POLN_ITEM_CLASS_NAME,
    TRIM(POLN_ITEM_DESC) AS POLN_ITEM_DESC,
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

where POLN_ITEM_NO NOT IN ('1', 'X', 'C', 'F', 'TAG', 'SPEC', 
                           'COIL PROCESS', 'WIRE16', 'WIRE14', 'WIRE14HRPO')

and substring(poln_item_no, 1, 2) between 12 and 67

and TRIM(SUBSTRING_INDEX(
            POLN_ITEM_DESC, ' ', 1)) not in ('**', 'COATED', 'MISCELLANEOUS', 
                                             'BOND', 'PTD', 'ALMZ', 'PTDCR', 'GVLM', 'GLVM', 'GLVM',
                                             'CRFH', 'PTDGVLM', 'EG', 'EMBGALV', 'PTDGALV', 
                                             'POTLDRY', 'GALVEMB', 'PTDHR', '2', 'HRPTD', 
                                             'SECONDARY', 'PAINTED', 'PTDGVLMGV', 'PTDGALV/GVLM',
                                             'HRFP', 'POTP', 'GF', 'FLPL')
and poln_order_qty > 0;



-- Quick Looks

    -- Full Table
    select * from po_history_lines_clean;