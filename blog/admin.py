from django.contrib import admin
from models import *
from django.forms.widgets import Textarea
from sugar.cache.utils import create_cache_key

class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}

admin.site.register(Category, CategoryAdmin)

class AudioFileInline(admin.TabularInline):
    model = AudioFile

class PostAdmin(admin.ModelAdmin):
    list_display  = ('title', 'publish', 'status', 'visits')
    list_filter   = ('publish', 'categories', 'status')
    search_fields = ('title', 'body')
    prepopulated_fields = {'slug': ('title',)}
    inlines = ( AudioFileInline,)

    blog_settings = Settings.get_current()
    
    if blog_settings != None and blog_settings.active_editor > 1 : 
        fieldsets = (
            (None, {
                'fields': ('title', 'slug', 'author',
                        'body', 'tease', 'status', 'allow_comments',
                        'publish', 'categories', 'tags', )
            }),

        )
    else:
        fieldsets = (
            (None, {
                'fields': ('title', 'slug', 'author', 'markup',
                    'body', 'tease', 'status', 'allow_comments',
                    'publish', 'categories', 'tags', )
            }),
            ('Converted markup', {
                'classes': ('collapse',),
                'fields': ('body_markup',),
            }),
        )
        
    def get_form(self, req, obj=None, **kwargs):
        # save the currently logged in user for later
        self.current_user = req.user
        return super(PostAdmin, self).get_form(req, obj, **kwargs)
    
    def formfield_for_dbfield(self, db_field, **kwargs):
        field = super(PostAdmin, self).formfield_for_dbfield(db_field, **kwargs) # Get the default field
        
        blog_settings = Settings.get_current()
        from django import forms
        from django.contrib.auth import models

        if db_field.name == 'author':
            queryset = models.User.objects.all()
            field = forms.ModelChoiceField(queryset=queryset, initial=self.current_user.id)

        return field

    def add_view(self, request, form_url='', extra_context=None):
        blog_settings = Settings.get_current()
        if blog_settings != None:
            active_editor = blog_settings.active_editor
        extra_context = { 'active_editor': active_editor }            
        return super(PostAdmin, self).add_view(request, form_url, extra_context)
        
    def change_view(self, request, object_id, extra_context=None):
        blog_settings = Settings.get_current()
        if blog_settings != None:
            active_editor = blog_settings.active_editor
        extra_context = { 'active_editor': active_editor }
        return super(PostAdmin, self).change_view(request, object_id, extra_context)

class SettingsAdmin(admin.ModelAdmin):

    fieldsets = (
            (None, {
                'fields': ('site', 'author_name', 'copyright', 'about',
                        'rss_url', 'twitter_url', 'email_subscribe_url', 'page_size',
                        'ping_google', 'disqus_shortname', 'active_editor','excerpt_length',)
            }),
            ('Meta options', {
                'classes': ('collapse',),
                'fields': ('meta_keywords', 'meta_description', ),
            }),

        )

class BlogRollAdmin(admin.ModelAdmin):

    list_display = ('name', 'url', 'sort_order', )
    list_editable = ('sort_order',)

admin.site.register(Post, PostAdmin)
admin.site.register(Settings, SettingsAdmin)
admin.site.register(BlogRoll, BlogRollAdmin)
