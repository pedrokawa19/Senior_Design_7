# Code Directory Guide

This directory contains data analysis and database query assets for the project. The Django dashboard application is separate, in `../web-django/`.
Changes made to code here needs to be implemented in the Django dashboard separately.

## Directory map

| Path | Contents |
| --- | --- |
| `R/` | R analysis scripts. |
| `python/src/` | Python scripts that are used in the dashboard. |
| `python/functions/` | Reusable Python tools. `bid_list/` contains the bid-list filtering notebook; `bid_lists/` contains example input workbooks. |
| `python/sandbox/` | Python notebook experiments and scratch work. |
| `sql/cleaned/` | SQL definitions for cleaned tables into views. |
| `sql/functions/` | Reusable SQL functions. |
| `sql/src/` | SQL queries that are used in the dashboard. |
| `sql/sandbox/` | SQL experiments and work in progress. |
| `ER Diagram.png` | Reference diagram for the data model. |

## Working with this code

- Keep experimental work in the relevant `sandbox/` directory. 
- Move it into `src/` or a reusable `functions/` location when it is ready for regular use.

## Inventory status values

The inventory quantity fields use these status values. **Values 1 and 2 together represent on-hand inventory.**

| Value | Field | Meaning |
| ---: | --- | --- |
| 1 | `VMIT-QTY-AVAIL` | Available to sell |
| 2 | `VMIT-QTY-ALLOC` | Allocated to a customer |
| 3 | `VMIT-QTY-SOLD` | Sold to a customer |
| 4 | `VMIT-QTY-USED` | Used to create sub-tags, such as leveling sheets or slitting coils |
| 5 | `VMIT-QTY-CM` | Credit memos |
| 6 | `VMIT-QTY-RETURN` | Purchase order returns |
| 9 | `VMIT-QTY-DELETED` | Deleted before receipt |

Keep these categories distinct when interpreting inventory quantities. In particular, a record marked deleted before receipt is not received inventory.

## What these statuses mean in practice

- **Credit memo (`VMIT-QTY-CM`)**: A quantity recorded in connection with a credit memo, an accounting document that credits or adjusts an amount related to a transaction. Treat it as a separate adjustment category, not as available stock.
- **Purchase order return (`VMIT-QTY-RETURN`)**: Material recorded as returned against a purchase order, typically sent back to the supplier. It should not be counted as inventory available to sell.
- **Deleted before receipt (`VMIT-QTY-DELETED`)**: A purchase or inventory record removed before the material was received. It represents no received physical stock.

These descriptions follow the field labels; confirm the exact transaction handling with the source-system documentation if a calculation depends on it.