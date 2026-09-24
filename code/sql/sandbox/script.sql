select * from items_clean order by item_number
limit 1000;


select * from vmitags_clean
order by vmit_item_no
limit 1000;

select * from po_history_lines_clean
order by POLN_DATE_GOODS_RECD desc, poln_item_no asc
limit 1000;