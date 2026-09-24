"""HTML pages. Every page requires a signed-in user.

Pages load their data from the JSON endpoints in ``views.api``. Database
settings are managed on the Profile page, not on the dashboard.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse

from ..credentials import CredentialStorageUnavailable, public_connection
from ..services import connections


@login_required
def dashboard(request):
    return render(request, "dashboard.html", {"active_tab": "dashboard"})


def _placeholder(request, tab, title):
    return render(
        request,
        "placeholder.html",
        {"active_tab": tab, "page_title": title, "page_message": f"This is the {title} page"},
    )


@login_required
def auction(request):
    return _placeholder(request, "auction", "Auction")


@login_required
def inventory(request):
    return _placeholder(request, "inventory", "Inventory")


@login_required
def model(request):
    return _placeholder(request, "model", "Model")


@login_required
def history(request):
    return redirect("history-purchases")


def _history_page(request, view_name, title, api_url_name):
    return render(
        request,
        "history.html",
        {
            "active_tab": "history",
            "history_view": view_name,
            "page_title": title,
            "api_url": reverse(api_url_name),
        },
    )


@login_required
def history_purchases(request):
    return _history_page(request, "purchases", "Purchase History", "purchase-history")


@login_required
def history_sales(request):
    return _history_page(request, "sales", "Sales History", "sales-history")


@login_required
def profile(request):
    """Account details plus the saved database connection."""
    storage_error = None
    try:
        connection = public_connection(connections.load_connection(request.user))
    except CredentialStorageUnavailable as error:
        connection = None
        storage_error = str(error)

    return render(
        request,
        "profile.html",
        {
            "active_tab": "profile",
            "saved_connection": connection,
            "storage_error": storage_error,
        },
    )
