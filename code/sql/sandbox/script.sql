
-- Debugging
SHOW FULL PROCESSLIST;
KILL QUERY 170;
EXPLAIN FORMAT=JSON FOR CONNECTION 170;


select 
polnf_key,
poln_item_no,
poln_item_class_no,
poln_item_desc,
poln_item_desc_pref,
poln_date_goods_recd
from po_history_lines_clean
limit 1000;


-- EXPLAIN FORMAT=JSON
SELECT
    -- Item Information
    v.vmitf_key,
    v.vmit_item_class,
    v.vmit_item_no,
    v.vmit_tag_desc,

    -- Buy Dates
    v.vmit_po_date,
    v.vmit_tag_po_date,
    pl.poln_deliv_date,
    pl.poln_date_goods_recd,

    -- Vendor
    pl.poln_vendor_name,

    -- Buy Quantity / Weight
    v.vmit_qty,
    pl.poln_order_qty,

    -- Costs
    v.vmit_cost,
    pl.poln_item_cost,
    ol.ordl_item_cost,
    pl.poln_rcvd_price,
    pl.poln_item_total_cost,
    pl.poln_total_cost,
    ol.ordl_total_cost,

    -- Sell Dates
    oh.ordh_ord_date,
    oh.ordh_inv_date,

    -- Customer
    oh.ordh_cust_no,

    -- Sell Quantity / Weight
    ol.ordl_order_qty,

    -- Revenues
    ol.ordl_item_rev,
    ol.ordl_total_rev,

    -- Profit
    ol.ordl_total_profit

FROM vmitags_clean v

LEFT JOIN po_history_lines_clean pl
    ON v.vmitf_key = pl.poln_vmi_tag_no
    AND v.vmit_poln_po_no = pl.poln_po_no
    AND v.vmit_poln_sub_po_no = pl.poln_sub_po_no
    AND v.vmit_poln_seq_no = pl.poln_seq_no

LEFT JOIN order_history_lines_clean ol
    ON v.vmitf_key = ol.ordl_vmit_tag_no

LEFT JOIN order_history_hdrs_clean oh
    ON ol.ordlf_ordh_key = oh.ordhf_key
limit 20;






-- working on inventory cost table 



SELECT * from po_history_lines_clean;

SET @as_of_date = '2026-09-28';

SELECT
    @as_of_date AS as_of_date,
    i.item_number,
    i.item_desc,

    COALESCE(t.quantity_bought, 0) AS quantity_bought,
    COALESCE(t.purchase_cost, 0) AS purchase_cost,

    ROUND(
        t.purchase_cost / NULLIF(t.quantity_bought, 0),
        6
    ) AS avg_purchase_cost_per_unit,

    COALESCE(t.quantity_sold, 0) AS quantity_sold,
    COALESCE(t.sales_revenue, 0) AS sales_revenue,

    ROUND(
        t.sales_revenue / NULLIF(t.quantity_sold, 0),
        6
    ) AS avg_selling_price_per_unit,

    COALESCE(t.cost_of_goods_sold, 0) AS cost_of_goods_sold,

    COALESCE(t.quantity_bought, 0)
        - COALESCE(t.quantity_sold, 0)
        AS estimated_quantity_remaining,

    COALESCE(t.purchase_cost, 0)
        - COALESCE(t.cost_of_goods_sold, 0)
        AS estimated_inventory_cost,

    ROUND(
        (COALESCE(t.purchase_cost, 0)
            - COALESCE(t.cost_of_goods_sold, 0))
        / NULLIF(
            COALESCE(t.quantity_bought, 0)
                - COALESCE(t.quantity_sold, 0),
            0
        ),
        6
    ) AS estimated_cost_per_remaining_unit

FROM items_clean i

LEFT JOIN (
    SELECT
        item_number,
        SUM(quantity_bought) AS quantity_bought,
        SUM(purchase_cost) AS purchase_cost,
        SUM(quantity_sold) AS quantity_sold,
        SUM(sales_revenue) AS sales_revenue,
        SUM(cost_of_goods_sold) AS cost_of_goods_sold

    FROM (
        -- Purchases through the selected date
        SELECT
            POLN_ITEM_NO AS item_number,
            CAST(POLN_ORDER_QTY AS DECIMAL(18,4))
                AS quantity_bought,
            POLN_TOTAL_COST AS purchase_cost,
            0 AS quantity_sold,
            0 AS sales_revenue,
            0 AS cost_of_goods_sold

        FROM po_history_lines_clean

        WHERE POLN_DATE_GOODS_RECD > '1900-01-01'
          AND POLN_DATE_GOODS_RECD <= @as_of_date

        UNION ALL

        -- Sales through the selected date
        SELECT
            l.ORDL_ITEM_NO AS item_number,
            0 AS quantity_bought,
            0 AS purchase_cost,
            CAST(l.ORDL_ORDER_QTY AS DECIMAL(18,4))
                AS quantity_sold,
            l.ORDL_TOTAL_REV AS sales_revenue,
            l.ORDL_TOTAL_COST AS cost_of_goods_sold

        FROM order_history_lines_clean l

        INNER JOIN order_history_hdrs_clean h
            ON l.ORDLF_ORDH_KEY = h.ORDHF_KEY

        WHERE h.ORDH_INV_DATE > '1900-01-01'
          AND h.ORDH_INV_DATE <= @as_of_date
    ) transactions

    GROUP BY item_number
) t
    ON i.item_number = t.item_number

ORDER BY i.item_number;



select * from vmitags_clean;



select * from vmitags_clean where vmit_qty_status = 4;


select * from po_history_lines_clean;

select * from order_history_lines_clean;


select poln_vmi_tag_no from po_history_lines_clean where poln_po_no = 3879;


select * from vmitags_clean where vmitf_key in (select concat('00', poln_vmi_tag_no) from po_history_lines_clean where poln_po_no = 3879);




select * from order_history_lines_clean;




SELECT t1.column1, t1.column2, t2.some_value
FROM table1 AS t1
INNER JOIN table2 AS t2
  ON t1.id = t2.id 
  AND t1.sub_id = t2.sub_id;;

drop view past_sales;