# Purchasing Optimization Model for Vision Metals

## Objective

The goal of this model is to help Vision Metals, a secondary metals distributor, make more informed bidding and buying decisions. The project uses historical purchases, market trends, and inventory levels to support purchasing decisions and stronger gross margins.

## Deliverable

The dashboard is designed to let purchasers upload bid lists, review market and inventory information, explore suggested bid ranges, and compare past transactions. It supports purchaser judgment and does not automatically submit bids.

The dashboard uses Django for backend request handling and server-rendered HTML templates for the user interface. SQL retrieves inventory and transaction data, while Python powers analytical models that generate purchasing insights and suggested bid ranges. It is planned to run on an always-on server inside Vision Metals' network, with VPN access for authorized remote users.

## Repository Diagram

[![GitDiagram](https://img.shields.io/badge/-GitDiagram-3776AB?style=flat&logo=github&logoColor=purple)](https://gitdiagram.com/pedrokawa19/senior_design_7)