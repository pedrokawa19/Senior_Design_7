CREATE OR REPLACE VIEW items_clean AS
SELECT

-- Item Info
    TRIM(item_number) AS item_number,
    STRIP_DIGITS(item_number) AS item_number_suff,
    TRIM(item_desc_1) AS item_desc,
    TRIM(SUBSTRING_INDEX(item_desc_1, ' ', 1)) AS item_class_name,
    CAST(item_class AS SIGNED) AS item_class_cd,

-- Vendor Info
    TRIM(item_vendor) AS item_vendor,

-- Cost Info
    CAST(item_avg_cost AS DECIMAL(10,2)) AS item_avg_cost,
    CAST(item_last_cost AS DECIMAL(10,2)) AS item_last_cost,
    CAST(item_onhand_cost AS DECIMAL(10,2)) AS item_onhand_cost,

-- Date Info
    CAST(item_lsale AS DATE) AS item_lsale_date,
    CAST(item_last_pur1 AS DATE) AS item_last_pur,

-- Quantity Info
    CAST(item_onord AS DECIMAL(10,2)) AS item_onord,
    CAST(item_qty_sold AS DECIMAL(10,2)) AS item_qty_sold,

-- Weight Info
    CAST(item_piece_wgt AS DECIMAL(10,2)) AS item_piece_wgt,

-- Current Financial Info
    CAST(item_cur_qty_sold AS DECIMAL(10,2)) AS item_cur_qty_sold,
    CAST(item_cur_dol_sold AS DECIMAL(10,2)) AS item_cur_dol_sold,
    CAST(item_cur_rec AS DECIMAL(10,2)) AS item_cur_rec,
    CAST(item_cur_adj AS DECIMAL(10,2)) AS item_cur_adj,

-- YTD Financial Info
    CAST(item_ytd_qty_sold AS DECIMAL(10,2)) AS item_ytd_qty_sold,
    CAST(item_ytd_dol_sold AS DECIMAL(10,2)) AS item_ytd_dol_sold,
    CAST(item_ytd_rec AS DECIMAL(10,2)) AS item_ytd_rec,
    CAST(item_ytd_profit AS DECIMAL(10,2)) AS item_ytd_profit,

-- Last Year Financial Info
    CAST(item_lyr_qty_sold AS DECIMAL(10,2)) AS item_lyr_qty_sold,
    CAST(item_lyr_dol_sold AS DECIMAL(10,2)) AS item_lyr_dol_sold,
    CAST(item_lyr_cost AS DECIMAL(10,2)) AS item_lyr_cost,
    
-- Other Info
    CAST(item_conv_factor AS DECIMAL(10,2)) AS item_conv_factor,
    TRIM(item_upc_no) AS item_upc_no,
    TRIM(item_alt_number) AS item_alt_number
FROM items
WHERE item_class BETWEEN 12 AND 67
    AND item_number != 0
HAVING item_number_suff NOT IN ('X', 'T', 'DEL', 'DROP')
    AND item_class_name NOT IN ('ALMZ', 'PTDCR', 'CLEAT', 'GVLM');


select * from items_clean;