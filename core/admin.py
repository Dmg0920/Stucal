from django.contrib import admin
from .models import Session, Material


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'created_at']
    list_filter = ['subject']
    search_fields = ['title', 'subject']


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ['date', 'time_start', 'time_end', 'status']
    list_filter = ['status', 'date']
    filter_horizontal = ['materials']
    date_hierarchy = 'date'
