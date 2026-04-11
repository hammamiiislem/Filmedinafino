from django.contrib import admin
from django.utils.translation import gettext as _
from .models import Event, EventMedia


class EventMediaInline(admin.TabularInline):
    model = EventMedia
    extra = 1


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'partner', 'start_date', 'status', 'visibility', 'is_boosted')
    list_filter = ('status', 'visibility', 'is_boosted', 'start_date')
    search_fields = ('title', 'description', 'partner__username', 'partner__email')
    inlines = [EventMediaInline]
    actions = ['approve_events', 'reject_events']

    def approve_events(self, request, queryset):
        rows_updated = queryset.update(status='APPROVED')
        if rows_updated == 1:
            message_bit = _("1 event was")
        else:
            message_bit = _("%s events were") % rows_updated
        self.message_user(request, _("%s successfully marked as approved.") % message_bit)
    approve_events.short_description = _("Mark selected events as Approved")

    def reject_events(self, request, queryset):
        rows_updated = queryset.update(status='REJECTED')
        if rows_updated == 1:
            message_bit = _("1 event was")
        else:
            message_bit = _("%s events were") % rows_updated
        self.message_user(request, _("%s successfully marked as rejected.") % message_bit)
    reject_events.short_description = _("Mark selected events as Rejected")


@admin.register(EventMedia)
class EventMediaAdmin(admin.ModelAdmin):
    list_display = ('event', 'type', 'uploaded_at')
    list_filter = ('type', 'uploaded_at')
