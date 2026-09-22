create or replace view items_clean as
select
    trim(item_number) as item_number,
    trim(item_desc_1) as item_desc,
    cast(item_avg_cost as decimal(10,2)) as item_avg_cost,
    cast(item_last_cost as decimal(10,2)) as item_last_cost,
    cast(item_onhand_cost as decimal(10,2)) as item_onhand_cost,
    cast(item_class as signed) as item_class_cd,
    trim(substring_index(item_desc_1, ' ', 1)) as item_class_name,
    cast(item_conv_factor as decimal(10,2)) as item_conv_factor,
    trim(item_vendor) as item_vendor,
    cast(item_lsale as date) as item_lsale_date,
    cast(item_onord as decimal(10,2)) as item_onord,
    cast(item_cur_qty_sold as decimal(10,2)) as item_cur_qty_sold,
    cast(item_cur_dol_sold as decimal(10,2)) as item_cur_dol_sold,
    cast(item_cur_rec as decimal(10,2)) as item_cur_rec,
    cast(item_cur_adj as decimal(10,2)) as item_cur_adj,
    cast(item_ytd_qty_sold as decimal(10,2)) as item_ytd_qty_sold,
    cast(item_ytd_dol_sold as decimal(10,2)) as item_ytd_dol_sold,
    cast(item_ytd_rec as decimal(10,2)) as item_ytd_rec,
    cast(item_ytd_profit as decimal(10,2)) as item_ytd_profit,
    cast(item_lyr_qty_sold as decimal(10,2)) as item_lyr_qty_sold,
    cast(item_lyr_dol_sold as decimal(10,2)) as item_lyr_dol_sold,
    cast(item_lyr_cost as decimal(10,2)) as item_lyr_cost,
    cast(item_qty_sold as decimal(10,2)) as item_qty_sold,
    cast(item_last_pur1 as date) as item_last_pur1,
    trim(item_upc_no) as item_upc_no,
    trim(item_alt_number) as item_alt_number,
    cast(item_piece_wgt as decimal(10,2)) as item_piece_wgt
    from items
    where item_class between 12 and 67
    and item_number != 0
    order by item_number asc;

