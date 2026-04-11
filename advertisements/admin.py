from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone

from .models import Advertisement, AdStatus


@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'user', 'format', 'status_badge',
        'image_preview', 'impressions', 'clicks', 'ctr_display',
        'start_date', 'end_date', 'created_at',
    ]
    list_filter  = ['status', 'format', 'file_type', 'created_at']
    search_fields = ['name', 'user__username', 'user__email', 'redirect_url']
    readonly_fields = [
        'id', 'file_type', 'impressions', 'clicks',
        'reviewed_by', 'reviewed_at', 'created_at', 'updated_at',
        'image_preview_large',
    ]
    ordering = ['-created_at']

    fieldsets = (
        ('Identité', {
            'fields': ('id', 'user', 'name')
        }),
        ('Contenu', {
            'fields': ('image', 'image_preview_large', 'file_type', 'redirect_url', 'format')
        }),
        ('Statut & Période', {
            'fields': ('status', 'start_date', 'end_date')
        }),
        ('Métriques', {
            'fields': ('impressions', 'clicks'),
            'classes': ('collapse',)
        }),
        ('Validation', {
            'fields': ('reviewed_by', 'reviewed_at', 'rejection_reason'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['approve_selected', 'reject_selected', 'pause_selected']

    def status_badge(self, obj):
        colors = {
            AdStatus.ACTIVE:   ('#EAF3DE', '#3B6D11'),
            AdStatus.PENDING:  ('#E6F1FB', '#185FA5'),
            AdStatus.REVIEW:   ('#E6F1FB', '#185FA5'),
            AdStatus.PAUSED:   ('#FAEEDA', '#854F0B'),
            AdStatus.REJECTED: ('#FCEBEB', '#A32D2D'),
            AdStatus.EXPIRED:  ('#F1EFE8', '#5F5E5A'),
        }
        bg, color = colors.get(obj.status, ('#F1EFE8', '#5F5E5A'))
        return format_html(
            '<span style="background:{};color:{};padding:2px 8px;border-radius:99px;font-size:11px">{}</span>',
            bg, color, obj.get_status_display()
        )
    status_badge.short_description = 'Statut'

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:36px;border-radius:4px;object-fit:cover;" />',
                obj.image.url
            )
        return '—'
    image_preview.short_description = 'Aperçu'

    def image_preview_large(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height:120px;max-width:400px;border-radius:6px;" />',
                obj.image.url
            )
        return '—'
    image_preview_large.short_description = 'Aperçu image'

    def ctr_display(self, obj):
        return f"{obj.ctr}%"
    ctr_display.short_description = 'CTR'

    # Actions admin
    @admin.action(description="Approuver les publicités sélectionnées")
    def approve_selected(self, request, queryset):
        updated = queryset.filter(
            status__in=[AdStatus.PENDING, AdStatus.REVIEW]
        ).update(
            status=AdStatus.ACTIVE,
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f"{updated} publicité(s) approuvée(s).")

    @admin.action(description="Rejeter les publicités sélectionnées")
    def reject_selected(self, request, queryset):
        updated = queryset.update(
            status=AdStatus.REJECTED,
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f"{updated} publicité(s) rejetée(s).")

    @admin.action(description="Mettre en pause les publicités sélectionnées")
    def pause_selected(self, request, queryset):
        updated = queryset.filter(status=AdStatus.ACTIVE).update(status=AdStatus.PAUSED)
        self.message_user(request, f"{updated} publicité(s) mise(s) en pause.")