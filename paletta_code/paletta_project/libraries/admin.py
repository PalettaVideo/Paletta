from django.contrib import admin
from .models import Library, LibraryMember

class LibraryAdmin(admin.ModelAdmin):
    list_display = ('name', 'LibraryAdmin', 'created_at')
    list_filter = ['LibraryAdmin']
    search_fields = ('name', 'description')
    list_per_page = 20

@admin.register(LibraryMember)
class LibraryMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'library', 'role', 'added_at')
    list_filter = ('role', 'added_at')
    search_fields = ('user__username', 'library__name')

admin.site.register(Library, LibraryAdmin)