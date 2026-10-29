from django.contrib import admin

from .models import Area, Posting, Slot

admin.site.register(Area)
admin.site.register(Slot)


@admin.register(Posting)
class PostingAdmin(admin.ModelAdmin):
    list_display = ("id", "owner", "kind", "area", "date", "court", "status")
    list_filter = ("kind", "status", "area")
    readonly_fields = (
        "owner",
        "kind",
        "area",
        "date",
        "slot",
        "court",
        "desired",
        "mode",
        "players_needed",
        "min_level",
        "max_level",
        "starts_at",
    )

    def has_add_permission(self, request):
        return False
