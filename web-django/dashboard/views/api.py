"""JSON endpoints used by the dashboard page.

These validate the request and shape the response. The work itself is done by
``dashboard.services``. Error responses stay generic so that database hosts,
account names, and credentials never reach the browser or the logs.
"""

import json
import logging
from datetime import date
from functools import wraps

from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from ..credentials import (
    ConnectionNotConfigured,
    CredentialStorageUnavailable,
    public_connection,
)
from ..forms import ConnectionForm, HistoryFilterForm
from ..models import SavedConnection
from ..services import connections, database, history, market, profitability
from ..services.history import HistoryQueryNotConfigured, InvalidHistorySort

logger = logging.getLogger(__name__)

REVEAL_MAX_ATTEMPTS = 5
REVEAL_LOCKOUT_SECONDS = 300


def api_login_required(view):
    """Return 401 JSON instead of redirecting browsers to the login page."""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"detail": "Authentication required."}, status=401)
        return view(request, *args, **kwargs)

    return wrapper


def _first_form_error(form):
    for errors in form.errors.values():
        if errors:
            return errors[0]
    return "The submitted database settings are invalid."


@api_login_required
@require_http_methods(["GET", "POST", "DELETE"])
def connection(request):
    if request.method == "DELETE":
        connections.delete_connection(request.user)
        return JsonResponse({"connection": None})

    if request.method == "GET":
        try:
            saved = connections.load_connection(request.user)
        except CredentialStorageUnavailable as error:
            return JsonResponse({"detail": str(error)}, status=503)
        return JsonResponse({"connection": public_connection(saved)})

    try:
        payload = json.loads(request.body or "{}")
    except ValueError:
        return JsonResponse({"detail": "Send the database settings as JSON."}, status=400)
    if not isinstance(payload, dict):
        return JsonResponse({"detail": "Send the database settings as JSON."}, status=400)

    form = ConnectionForm(payload)
    if not form.is_valid():
        return JsonResponse({"detail": _first_form_error(form)}, status=400)

    try:
        saved = connections.save_connection(request.user, form.cleaned_data)
    except CredentialStorageUnavailable as error:
        return JsonResponse({"detail": str(error)}, status=503)

    if saved is None:
        return JsonResponse(
            {"detail": "A password is required for a new connection."}, status=400
        )
    return JsonResponse({"connection": public_connection(saved)})


@api_login_required
@require_POST
def connection_password(request):
    """Reveal the saved database password after the user confirms their own.

    Re-authenticating keeps a borrowed session from exposing a client
    credential with a single click, and repeated failures lock the attempt out.
    """
    try:
        payload = json.loads(request.body or "{}")
    except ValueError:
        return JsonResponse({"detail": "Send your account password as JSON."}, status=400)
    if not isinstance(payload, dict):
        return JsonResponse({"detail": "Send your account password as JSON."}, status=400)

    attempts_key = f"reveal-attempts:{request.user.pk}"
    if cache.get(attempts_key, 0) >= REVEAL_MAX_ATTEMPTS:
        logger.warning("Reveal attempts locked out for user id %s", request.user.id)
        return JsonResponse(
            {"detail": "Too many attempts. Wait a few minutes and try again."}, status=429
        )

    if not request.user.check_password(payload.get("account_password") or ""):
        cache.set(attempts_key, cache.get(attempts_key, 0) + 1, REVEAL_LOCKOUT_SECONDS)
        return JsonResponse({"detail": "That is not your account password."}, status=403)

    cache.delete(attempts_key)

    try:
        saved_settings = connections.require_connection(request.user)
    except ConnectionNotConfigured as error:
        return JsonResponse({"detail": str(error)}, status=409)
    except CredentialStorageUnavailable as error:
        return JsonResponse({"detail": str(error)}, status=503)

    response = JsonResponse({"password": saved_settings["password"]})
    response["Cache-Control"] = "no-store"
    return response


@api_login_required
@require_POST
def verify_database(request):
    try:
        saved_settings = connections.require_connection(request.user)
    except ConnectionNotConfigured as error:
        return JsonResponse({"detail": str(error)}, status=409)
    except CredentialStorageUnavailable as error:
        return JsonResponse({"detail": str(error)}, status=503)

    try:
        database.verify_database_connection(saved_settings)
    except Exception:
        # The driver error can name the host and account, so it is not logged or returned.
        logger.warning("Database verification failed for user id %s", request.user.id)
        return JsonResponse(
            {"detail": "Unable to connect to the database with the saved settings."}, status=503
        )
    return JsonResponse({"status": "connected"})


@api_login_required
@require_GET
def profitable_products(request):
    try:
        saved_settings = connections.require_connection(request.user)
    except ConnectionNotConfigured as error:
        return JsonResponse({"detail": str(error)}, status=409)
    except CredentialStorageUnavailable as error:
        return JsonResponse({"detail": str(error)}, status=503)

    try:
        return JsonResponse({"products": profitability.get_profitable_products(saved_settings)})
    except Exception:
        logger.warning("Profitability query failed for user id %s", request.user.id)
        return JsonResponse({"detail": "Unable to load profitability data."}, status=503)


@api_login_required
@require_GET
def index_performance(request):
    try:
        start_date = date.fromisoformat(request.GET["start_date"])
        end_date = date.fromisoformat(request.GET["end_date"])
    except KeyError:
        return JsonResponse({"detail": "Start and end dates are required."}, status=400)
    except ValueError:
        return JsonResponse({"detail": "Enter valid start and end dates."}, status=400)

    try:
        return JsonResponse(
            market.get_index_performance(start_date, end_date, request.GET.get("ticker", "SLX"))
        )
    except ValueError as error:
        return JsonResponse({"detail": str(error)}, status=400)
    except Exception:
        logger.warning("Market data request failed for user id %s", request.user.id)
        return JsonResponse({"detail": "Unable to load market data."}, status=503)


def _history_response(request, loader, label):
    form = HistoryFilterForm(request.GET)
    if not form.is_valid():
        return JsonResponse({"detail": _first_form_error(form)}, status=400)
    try:
        saved_settings = connections.require_connection(request.user)
    except ConnectionNotConfigured as error:
        return JsonResponse({"detail": str(error)}, status=409)
    except CredentialStorageUnavailable as error:
        return JsonResponse({"detail": str(error)}, status=503)

    try:
        version = SavedConnection.objects.get(user=request.user).updated_at.isoformat()
        data = form.cleaned_data
        response = JsonResponse(loader(
            saved_settings, user_id=request.user.pk, connection_version=version,
            filters={name: data[name] for name in ("start_date", "end_date", "item", "party")},
            page=data["page"] or 1, refresh=data["refresh"] == "1",
            sort_column=data["sort_column"], sort_direction=data["sort_direction"],
        ))
        response["Cache-Control"] = "no-store"
        return response
    except InvalidHistorySort as error:
        return JsonResponse({"detail": str(error)}, status=400)
    except HistoryQueryNotConfigured as error:
        return JsonResponse({"detail": str(error)}, status=501)
    except history.InvalidHistoryDate as error:
        logger.warning("%s query failed for user id %s: invalid order-date data",
                       label, request.user.id)
        return JsonResponse({"detail": str(error)}, status=503)
    except Exception as error:
        logger.warning("%s query failed for user id %s (exception type: %s)",
                       label, request.user.id, type(error).__name__)
        return JsonResponse({"detail": f"Unable to load {label}."}, status=503)


@api_login_required
@require_GET
def purchase_history(request):
    return _history_response(request, history.get_purchase_history, "purchase history")


@api_login_required
@require_GET
def sales_history(request):
    return _history_response(request, history.get_sales_history, "sales history")
