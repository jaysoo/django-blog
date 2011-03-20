from django.core.cache import cache
from models import Settings
import twitter
import urllib2
from django.core.urlresolvers import reverse
from django_twitter.models import TwitterAccount
from django.contrib.sites.models import Site
from django.conf import settings

def invalidate_settings_cache(sender=None, instance=None, isnew=False, **kwargs):

    if isnew:
        return

    site_id = instance.site.id
    key = create_cache_key(Settings, field='site__id', field_value=site_id)
    #invalidate cache, set to None for 5 seconds to safegaurd
    #against race condition; concept borrowed from mmalone's django-caching
    cache.set(key, None, 5)

def post_to_twitter(sender, instance, **kwargs):
    """ 
    Post new saved, "published" Tweet objects to Twitter.
    """

    #confirm the post is a Public status, according to blog
    status = getattr(instance, "status", 1)
    if status == 1:
        return False

    #if the instance already existed
    if instance.pk:
        #grab the previous instance of the object
        try:
            prior_instance = instance._default_manager.get(pk=instance.pk)
            prior_status = getattr(prior_instance, "status", 1)
            #if this post was published
            if prior_status == 2:
                return False
        except:
            #todo: better logging/handling
            return False
        
    accounts = TwitterAccount.objects.all()
    for account in accounts:

        current_domain = Site.objects.get_current().domain
        url = "http://%s%s" % (current_domain, instance.get_absolute_url())

        prefix_message = instance.tease
        if not prefix_message:
            prefix_message = "New Blog Post"

        mesg = "%s - %s" % (prefix_message, url)

        consumer_key = settings.TWITTER_CONSUMER_KEY
        consumer_secret = settings.TWITTER_CONSUMER_SECRET
        access_key = account.access_token_key
        access_secret = account.access_token_secret

        try:
            api = twitter.Api(consumer_key=consumer_key, 
                    consumer_secret=consumer_secret,
                    access_token_key=access_key,
                    access_token_secret=access_secret)
            status = api.PostUpdate(mesg)
        except urllib2.HTTPError, ex:
           return False
