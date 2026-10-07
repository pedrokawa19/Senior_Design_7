-- Dashboard code: web-django/dashboard/services/profitability.py:7
-- Dashboard caller: web-django/dashboard/views/api.py:161
-- Last updated: 2026-10-06

create or replace view ytd_profit_per_class as
select 
    item_class_name,
    sum(item_ytd_profit) as ytd_profit_per_class,
    round(sum(item_ytd_profit) / (
        select sum(item_ytd_profit)
        from items_clean
    ) * 100, 2) as profit_share
 from items_clean
group by item_class_name
order by ytd_profit_per_class desc
limit 5;


select *
from ytd_profit_per_class;