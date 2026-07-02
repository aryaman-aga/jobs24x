from django.contrib import admin
from .models import BlogPost

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author_name', 'is_published', 'published_at']
    list_filter = ['is_published']
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ['title', 'content']
