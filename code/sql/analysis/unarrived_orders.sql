-- Orders that have not arrived
select * from po_history_lines_clean
where poln_date_goods_recd is null
order by poln_deliv_date desc;