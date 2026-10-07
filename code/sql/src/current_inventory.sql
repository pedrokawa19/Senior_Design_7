-- Dashboard code: web-django/dashboard/services/inventory.py:61
-- Dashboard caller: web-django/dashboard/views/api.py:241
-- Last updated: 2026-10-07

create or replace view current_inventory as
select 
vmitf_key,
vmit_item_no,
vmit_tag_desc,
vmit_parent_tag_no,
vmit_org_tag_no,
vmit_poln_po_no,
vmit_poln_sub_po_no,
vmit_poln_seq_no,
vmit_po_date,
vmit_qty,
vmit_piece_cnt,
vmit_cost,
vmit_qty_status,
vmit_order_cust,
vmit_bin_loc,
vmit_defect,
vmit_hardness,
vmit_grade,
vmit_surface,
vmit_coating_wgt,
vmit_yield,
vmit_tensile,
vmit_elongation
from vmitags_clean where vmit_qty_status in (1, 2);


select * from current_inventory order by vmit_po_date desc;