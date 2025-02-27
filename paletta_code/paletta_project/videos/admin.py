from django.contrib import admin
from .models import Category, Tag, Video

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
  list_display = ('title', 'category', 'uploader', 'upload_date')
  list_filter = ('category', 'tags', 'uploader', 'upload_date')
  search_fields = ('title', 'description')
  date_hierarchy = 'upload_date'
  list_per_page = 20

admin.site.register(Category)
admin.site.register(Tag)