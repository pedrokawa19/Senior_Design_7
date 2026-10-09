CREATE OR REPLACE VIEW order_history_lines_clean AS
SELECT
-- Sale IDs
    ORDLF_KEY,
    ORDLF_ORDH_KEY,
    ORDL_ORDER_NO,
    ORDL_SUB_ORDER_NO,
    ORDL_SEQ_NO,
    ORDL_PARENT_SEQ_NO,
    TRIM(ORDL_CUST_NO) AS ORDL_CUST_NAME,

-- Item Info
    TRIM(ORDL_ITEM_NO) AS ORDL_ITEM_NO,
    CAST(LEFT(TRIM(ORDL_ITEM_NO), 2) AS UNSIGNED) AS ORDL_ITEM_CLASS_NO,
    SUBSTRING_INDEX(TRIM(ORDL_ITEM_DESC), ' ', 1) AS ORDL_ITEM_CLASS_NAME,
    TRIM(ORDL_ITEM_DESC) AS ORDL_ITEM_DESC,
    SUBSTRING_INDEX(SUBSTRING_INDEX(TRIM(ORDL_ITEM_DESC), ' ', 2),' ',-1) AS ORDL_ITEM_GAUGE,
    ORDL_VMIT_TAG_NO,

-- Date Info
    DATE_FORMAT(CAST(oh.ordh_ord_date AS DATE), '%Y-%m-%d') AS ORDH_ORD_DATE,

-- Quantity Info
    CAST(ORDL_ORDER_QTY AS UNSIGNED) AS ORDL_ORDER_QTY,

-- Financial Info
    CAST(ORDL_ITEM_PRICE AS DECIMAL(10,2)) AS ORDL_ITEM_REV,
    CAST(ORDL_ITEM_COST AS DECIMAL(10,2)) AS ORDL_ITEM_COST,
    CAST(ORDL_EXT_AMT AS DECIMAL(10,2)) AS ORDL_TOTAL_REV,
    CAST(ORDL_EXT_COST AS DECIMAL(10,2)) AS ORDL_TOTAL_COST,
    CAST(ORDL_EXT_AMT - ORDL_EXT_COST AS DECIMAL(10,2)) AS ORDL_TOTAL_PROFIT,

-- Other Info
    CAST(ORDL_CONV_FACTOR AS DECIMAL(10,2)) AS ORDL_CONV_FACTOR

FROM order_history_lines ol
    LEFT JOIN order_history_hdrs_clean oh ON ol.ordlf_ordh_key = oh.ordhf_key

WHERE 

-- Class Filter
    CAST(LEFT(TRIM(ORDL_ITEM_NO), 2) AS UNSIGNED) BETWEEN 12 AND 67

-- Quantity Filter
    AND ORDL_ORDER_QTY > 0

-- Date Filter
    AND oh.ordh_ord_date > '2014-01-01'

-- Item Number Filter
    AND TRIM(ORDL_ITEM_NO) NOT IN ('C', 'F', 'EXPORT', '1', 'x', 'X',
                                 'S', 'D', 'TAXABLE', 'NON-TAXABLE', 'T')

-- VMI Tag Null Filter
-- AND ORDL_VMIT_TAG_NO IS NOT NULL

-- Item Type Filter
    AND STRIP_DIGITS(TRIM(ORDL_ITEM_NO)) NOT IN ('M', 'T', 'X', 'DROP', 'SHEET', 'PLATE')

-- Item Description Filter
    AND SUBSTRING_INDEX(TRIM(ORDL_ITEM_DESC), ' ', 1) NOT IN 
        ('ALMZ', 'ADJUSTMENT', 'ALZM', 'MISCELLANEOUS', 'PTD', 'BOND', 
         'PL', 'FLPL', 'AZ50', 'EG', 'GA/GI', 'SCRAP', 'GF', 'CLEAT', 
         'POTP', 'POTLDRY', 'SEC', '4', '5','', 'GVLM', 'GLVM', 'HRFL', 
         'CRFH', 'GVLM', 'PTDGALV', 'PTDCR', 'PTDGVLM', 'PTDHR', 'PTDGV', 
         '36"','20GA', '24GA', 'EmbGALV', '7GA', '26GA', 'TRTGALV', '18GA', 
         'GALVEMB', '48"', 'G40', '.030', 'GALV.072', 'GALV.057', 'GALV.051', 
         'HRTP', 'HRP_DRY')

-- Random PLATE item that idk how else to remove without making this too long.
    AND ORDLF_KEY <> 00248901000256
;



-- Full ol
select * from order_history_lines_clean;