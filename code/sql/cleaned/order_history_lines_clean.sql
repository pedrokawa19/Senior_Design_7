CREATE OR REPLACE VIEW order_history_lines_clean AS
SELECT
-- ORDER NUMBER INFO
    ORDLF_KEY,
    ORDLF_ORDH_KEY,
    ORDL_ORDER_NO,
    ORDL_SUB_ORDER_NO,
    ORDL_SEQ_NO,
    ORDL_PARENT_SEQ_NO,
    TRIM(ORDL_CUST_NO) AS ORDL_CUST_NAME,

-- ITEM NUMBER AND DESCTIPTION INFO AND CLEAN UP
    TRIM(ORDL_ITEM_NO) AS ORDL_ITEM_NO,
    CAST(LEFT(TRIM(ORDL_ITEM_NO), 2) AS UNSIGNED) AS ITEM_CLASS_NO,
    CAST(ORDL_ITEM_CLASS AS UNSIGNED) AS ORDL_ITEM_CLASS_NO,
    TRIM(ORDL_ITEM_DESC) AS ORDL_ITEM_DESC,
    SUBSTRING_INDEX(TRIM(ORDL_ITEM_DESC), ' ', 1) AS ORDL_ITEM_CLASS_NAME,
    SUBSTRING_INDEX(SUBSTRING_INDEX(TRIM(ORDL_ITEM_DESC), ' ', 2),' ',-1) AS ORDL_ITEM_GAUGE,
    CASE
        WHEN UPPER(TRIM(ORDL_ITEM_DESC)) REGEXP '[[:<:]]COIL[[:>:]]'
        OR UPPER(TRIM(ORDL_ITEM_NO)) LIKE '%COIL%' THEN 'COIL'

        WHEN UPPER(TRIM(ORDL_ITEM_DESC)) REGEXP '[[:<:]]SHEET[[:>:]]'
        OR UPPER(TRIM(ORDL_ITEM_NO)) LIKE '%SHEET%' THEN 'SHEET'

        WHEN UPPER(TRIM(ORDL_ITEM_DESC)) REGEXP '[[:<:]]PLATE[[:>:]]'
        OR UPPER(TRIM(ORDL_ITEM_NO)) LIKE '%PLATE%' THEN 'PLATE'

        ELSE 'COIL'
    END AS ORDL_ITEM_TYPE,

-- Tag Number
    ORDL_VMIT_TAG_NO,

    -- QUANTITY, REVENUE, COST, AND PROFIT
    CAST(ORDL_ORDER_QTY AS UNSIGNED) AS ORDL_ORDER_QTY,
    CAST(ORDL_ITEM_PRICE AS DECIMAL(10,2)) AS ORDL_ITEM_REV,
    CAST(ORDL_ITEM_COST AS DECIMAL(10,2)) AS ORDL_ITEM_COST,
    CAST(ORDL_EXT_AMT AS DECIMAL(10,2)) AS ORDL_TOTAL_REV,
    CAST(ORDL_EXT_COST AS DECIMAL(10,2)) AS ORDL_TOTAL_COST,
    CAST(ORDL_EXT_AMT - ORDL_EXT_COST AS DECIMAL(10,2)) AS ORDL_TOTAL_PROFIT,
    CAST(ORDL_CONV_FACTOR AS DECIMAL(10,2)) AS ORDL_CONV_FACTOR,

-- ITEM LOCATIONS, MEASUREMENTS, ETC
    CAST(ORDL_PRICE_CD AS UNSIGNED) AS ORDL_PRICE_CD

FROM order_history_lines


-- Managerial Filter
WHERE TRIM(ORDL_ITEM_NO) NOT IN ('C', 'F', 'EXPORT', '1', 'x', 'X',
                                 'S', 'D', 'TAXABLE', 'NON-TAXABLE', 'T')

-- Class Number Filter
AND CAST(LEFT(TRIM(ORDL_ITEM_NO), 2) AS UNSIGNED) BETWEEN 12 AND 67

-- Quantity Filter
AND ORDL_ORDER_QTY > 0

-- -- VMI Tag Null Filter
-- AND ORDL_VMIT_TAG_NO IS NOT NULL


-- Description Filter
AND ORDL_ITEM_DESC NOT IN ('******* CREDIT MEMO ********', 
                           '____________________________')

-- Item Type Filter
AND STRIP_DIGITS(TRIM(ORDL_ITEM_NO)) NOT IN ('M', 'T', 'X', 'DROP', 'SHEET', 'PLATE')

-- Item Description Filter
AND SUBSTRING_INDEX(TRIM(ORDL_ITEM_DESC), ' ', 1) NOT IN ('ALMZ', 'ADJUSTMENT', 'ALZM', 'MISCELLANEOUS', 
                                                          'PTD', 'BOND', 'PL', 'FLPL', 'AZ50', 'EG', 'GA/GI', 
                                                          'SCRAP', 'GF', 'CLEAT', 'POTP', 
                                                          'POTLDRY', 'SEC', '4', '5','', 'GVLM', 'GLVM', 'HRFL', 'CRFH', 
                                                          'GVLM', 'PTDGALV', 'PTDCR', 'PTDGVLM', 'PTDHR', 'PTDGV', '36"',
                                                          '20GA', '24GA', 'EmbGALV', '7GA', '26GA', 'TRTGALV', '18GA', 'GALVEMB', 
                                                          '48"', 'G40', '.030', 'GALV.072', 'GALV.057', 'GALV.051')

-- Random PLATE item that idk how else to remove without making this too long.
and ORDLF_KEY <> 00248901000256
;