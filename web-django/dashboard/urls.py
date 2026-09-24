"""Which URL runs which view. Routing only -- no logic lives here."""

from django.urls import path

from .views import api, auth, pages

urlpatterns = [
    # Account access
    path("login/", auth.login_view, name="login"),
    path("signup/", auth.signup_view, name="signup"),
    path("logout/", auth.logout_view, name="logout"),
    path("profile/", pages.profile, name="profile"),
    # Pages
    path("", pages.dashboard, name="dashboard"),
    path("auction/", pages.auction, name="auction"),
    path("history/", pages.history, name="history"),
    path("history/purchases/", pages.history_purchases, name="history-purchases"),
    path("history/sales/", pages.history_sales, name="history-sales"),
    path("inventory/", pages.inventory, name="inventory"),
    path("model/", pages.model, name="model"),
    # JSON endpoints used by the pages
    path("api/connection", api.connection, name="connection"),
    path("api/connection/verify", api.verify_database, name="verify-database"),
    path("api/connection/password", api.connection_password, name="connection-password"),
    path("api/profitable-products", api.profitable_products, name="profitable-products"),
    path("api/index-performance", api.index_performance, name="index-performance"),
    path("api/history/purchases", api.purchase_history, name="purchase-history"),
    path("api/history/sales", api.sales_history, name="sales-history"),
]
