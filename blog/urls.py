from django.conf.urls.defaults import *
import views as views
from feeds import BlogPostsFeed


urlpatterns = patterns('',

    url(r'^(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})/(?P<slug>[-\w]+)/$',
        view=views.post_detail,
        name='blog_detail_month_numeric'),

    url(r'^(?P<year>\d{4})/(?P<month>\w{3})/(?P<day>\d{1,2})/(?P<slug>[-\w]+)/$',
        view=views.post_detail,
        name='blog_detail'),

    url(r'^(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})/$',
        view=views.post_archive_day,
        name='blog_archive_day'),

    url(r'^(?P<year>\d{4})/(?P<month>\d{1,2})/$',
        view=views.post_archive_month,
        name='blog_archive_month'),

    url(r'^(?P<year>\d{4})/$',
        view=views.post_archive_year,
        name='blog_archive_year'),

    url(r'^categories/(?P<slug>[-\w]+)/$',
        view=views.category_detail,
        name='blog_category_detail'),

    url (r'^categories/$',
        view=views.category_list,
        name='blog_category_list'),

    url(r'^tags/(?P<slug>[-\w]+)/$',
        view=views.tag_detail,
        name='blog_tag_detail'),

    url (r'^search/$',
        view=views.search,
        name='blog_search'),

    url(r'^page/(?P<page>\w)/$',
        view=views.post_list,
        name='blog_index_paginated'),

    url(r'^$',
        view=views.post_list,
        name='blog_index'),

    (r'^feed/$', BlogPostsFeed()),
)
