select * 
from items_clean i
right join vmitags_clean v
on i.item_number = v.vmit_item_no 
order by vmit_po_date desc
limit 1000;