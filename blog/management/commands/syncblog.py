from django.core.management.base import BaseCommand, CommandError
from basic.blog.models import Post
from datetime import datetime
from math import log10

class Command(BaseCommand):
    help = 'Syncs popularity for blog posts'

    def handle(self, *args, **options):
        posts = Post.objects.published()
        for post in posts:
            B = datetime(2010, 1, 1, 0, 0, 0)
            A = post.modified
            t = (A - B).seconds
            x = post.visits
            y = 1 if x > 0 else 0
            z = x if x >= 1 else 1
            p = log10(z) + (y*t)/45000
            print 'Setting popularity=%s for "%s"' % (p, post.title)
            post.popularity = p
            post.save()


