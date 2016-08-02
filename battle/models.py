from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible  # needed to support Python 2
class Battle(models.Model):
    battle_name = models.CharField(max_length=100)
    hashtag1 = models.CharField(max_length=500)
    hashtag1_typos = models.CharField(null=True, max_length=100, blank=True)
    hashtag2 = models.CharField(max_length=500)
    hashtag2_typos = models.CharField(null=True, max_length=100, blank=True)
    started_at = models.CharField(max_length=100)
    ended_at = models.CharField(max_length=100)
    winner = models.CharField(null=True, max_length=500, blank=True)
    status = models.CharField(max_length=100)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="+")

    def __unicode__(self):
        return self.battle_name

    def __str__(self):
        return str(self.battle_name)

    def get_absolute_url(self):
        return reverse('battle:battle_edit', kwargs={'pk': self.pk})