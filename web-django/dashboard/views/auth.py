"""Account access: sign up, log in, and log out."""

from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from ..forms import SignupForm
from ..services.auction_storage import cleanup_after_login


def _render_login(request, login_form, signup_form, active_mode):
    return render(
        request,
        "login.html",
        {"login_form": login_form, "signup_form": signup_form, "active_mode": active_mode},
    )


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    form = AuthenticationForm(request, data=request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        cleanup_after_login(user.pk)
        return redirect("dashboard")

    return _render_login(request, form, SignupForm(), "login")


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method != "POST":
        return redirect("login")

    form = SignupForm(request.POST)
    if form.is_valid():
        login(request, form.save())
        return redirect("dashboard")

    return _render_login(request, AuthenticationForm(request), form, "signup")


@require_POST
def logout_view(request):
    logout(request)
    return redirect("login")
