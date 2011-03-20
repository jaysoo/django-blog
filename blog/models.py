from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.db.models import permalink
from django.contrib.auth.models import User
from django.contrib.sitemaps import ping_google
from django.conf import settings
from tagging.fields import TagField
from managers import PublicManager
from django.contrib.sites.models import Site
import datetime
import tagging
from django_markup.fields import MarkupField
from django_markup.markup import formatter
from django.conf import settings
from django.utils.safestring import mark_safe
from django.core.cache import cache
from django.utils.text import truncate_words
from sugar.cache.utils import create_cache_key

from django.db.models import signals
from django.dispatch import dispatcher

class Category(models.Model):
    """Category model."""
    title       = models.CharField(_('title'), max_length=100)
    slug        = models.SlugField(_('slug'), unique=True)

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')
        db_table = 'blog_categories'
        ordering = ('title',)

    class Admin:
        pass

    def __unicode__(self):
        return u'%s' % self.title

    @permalink
    def get_absolute_url(self):
        return ('blog_category_detail', None, {'slug': self.slug})


class Post(models.Model):
    """Post model."""
    STATUS_CHOICES = (
        (1, _('Draft')),
        (2, _('Public')),
    )
    title           = models.CharField(_('title'), max_length=200)
    slug            = models.SlugField(_('slug'), unique_for_date='publish')
    author          = models.ForeignKey(User, blank=True, null=True)

    markup          = MarkupField(default='markdown')
    body            = models.TextField(_('body'), )
    tease           = models.TextField(_('tease'), blank=True, max_length=120, help_text=_('Teaser text prepended to post URL on Twitter.'))

    body_markup     = models.TextField(editable=True, blank=True, null=True)
    visits          = models.IntegerField(_('visits'), default=0, editable=False) #to keep track of most popular posts
    status          = models.IntegerField(_('status'), choices=STATUS_CHOICES, default=2)
    allow_comments  = models.BooleanField(_('allow comments'), default=True)
    publish         = models.DateTimeField(_('publish'), default=datetime.datetime.now)
    created         = models.DateTimeField(_('created'), auto_now_add=True)
    modified        = models.DateTimeField(_('modified'), auto_now=True)
    categories      = models.ManyToManyField(Category, blank=True)
    tags            = TagField()
    objects         = PublicManager()

    class Meta:
        verbose_name = _('post')
        verbose_name_plural = _('posts')
        db_table  = 'blog_posts'
        ordering  = ('-publish',)
        get_latest_by = 'publish'

    class Admin:
        list_display  = ('title', 'publish', 'status')
        list_filter   = ('publish', 'categories', 'status')
        search_fields = ('title', 'body')

    class ProxyMeta:
        title = 'title'
        description = 'body_markup'
        tags = 'tags'
        pub_date = 'publish'
        active = {'status':2}

    def __unicode__(self):
        return u'%s' % self.title

    def save(self, *args, **kwargs):
        blog_settings = Settings.get_current()

        if blog_settings.active_editor > 1:
            self.markup = "none"
            self.body_markup = self.body
        else:                
            self.body_markup = mark_safe(formatter(self.body, filter_name=self.markup))
        super(Post, self).save(*args, **kwargs)

        ping_google = getattr(blog_settings,"ping_google", False)
        
        if ping_google:
            try:
                ping_google()
            except:
                pass

    @permalink
    def get_absolute_url(self):
        return ('blog_detail_month_numeric', None, {
            'year': self.publish.year,
            'month': self.publish.strftime('%m').lower(),
            'day': self.publish.day,
            'slug': self.slug
        })

    def get_previous_post(self):
        return self.get_previous_by_publish(status__gte=2)

    def get_next_post(self):
        return self.get_next_by_publish(status__gte=2)

    @property
    def get_meta_keywords(self):
        if self.tags == '':
            return Settings.get_current().meta_keywords
        else:
            return self.tags

    @property
    def get_meta_description(self):
        if self.tease == '':
            return Settings.get_current().meta_description
        else:
            return truncate_words(self.tease, 255)

class Settings(models.Model):
    '''
    Global settings for the blog.

    The class name is plural because "Setting" singular implies one and this is a collection of settings.

    Possible: dynamic settings could be designed at some point to allow the user to add settings as they wish.
    '''

    EDITOR_CHOICES = (
        (1, _('Text')),
        (2, _('Django-WYSIWYG')),
    )
    site = models.ForeignKey(Site, unique=True)

    #denormalized to reduce queries
    site_name = models.CharField(max_length=50, editable=False)
    author_name = models.CharField(_('author name'), max_length=255, blank=True,
                null=True)
    copyright = models.CharField(_('copyright'), max_length=255, blank=True, null=True)
    about = models.TextField(_('about'), help_text=_('Accepts RAW html. By default, appears in right rail.'),
                blank=True, null=True)

    twitter_url = models.URLField(_('twitter url'), verify_exists=False, blank=True, null=True)
    rss_url = models.URLField(_('rss url'), verify_exists=False, blank=True, null=True,
                help_text=_('The location of your RSS feed. Often used to wire up feedburner.'))
    email_subscribe_url = models.URLField(_('subscribe via email url'),
                verify_exists=False, blank=True, null=True)
    page_size = models.PositiveIntegerField(_('page size'), default=20)
    ping_google = models.BooleanField(_('ping google'), default=False)
    disqus_shortname = models.CharField(_('disqus shortname'), max_length=255, blank=True, null=True)

    meta_keywords = models.TextField(_('meta keywords'), blank=True, null=True)
    meta_description = models.TextField(_('meta description'), blank=True, null=True)
    active_editor = models.IntegerField(_('editor'), choices=EDITOR_CHOICES, default=1)
    excerpt_length = models.IntegerField(_('excerpt length'), default=500, 
                    help_text=_('The character length of the post body field displayed in RSS templates.'))

    class Meta:
        verbose_name = _('settings')
        verbose_name_plural = _('settings')

    def __unicode__(self):
        return "%s-settings" % self.site.name

    def delete(self, *args, **kwargs):
        if settings.SITE_ID != self.site.id:
            super(Settings, self).delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.site_name = self.site.name
        super(Settings, self).save(*args, **kwargs)

    @staticmethod
    def get_current():
        site = Site.objects.get_current()
        key = create_cache_key(Settings, field='site__id', field_value=site.id)
        blog_settings = cache.get(key, None)
        if blog_settings is None:
            try:
                blog_settings = Settings.objects.get(site=site)
                cache.add(key, blog_settings)
            except Settings.DoesNotExist:
                return None
        return blog_settings


class BlogRoll(models.Model):
    '''

    Other blogs you follow.

    '''

    name = models.CharField(max_length=100)
    url = models.URLField(verify_exists=False)
    sort_order =  models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ('sort_order', 'name',)
        verbose_name = _('blog roll')
        verbose_name_plural = _('blog roll')

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return self.url
