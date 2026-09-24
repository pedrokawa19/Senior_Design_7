from django.contrib import admin

from .models import SavedConnection


@admin.register(SavedConnection)
class SavedConnectionAdmin(admin.ModelAdmin):
    """Administrators can audit and revoke saved connections but never read the credentials."""

    list_display = ("user", "updated_at")
    search_fields = ("user__username",)
    readonly_fields = ("user", "updated_at")
    fields = ("user", "updated_at")

    def has_add_permission(self, request):
        return False
