# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User

class OwnedObject(models.Model):
    owner = models.ForeignKey(User)

    def save(self, force_insert=False, force_update=False, using=None, user=None):
        if user:
            owner_set = True
            try:
                self.owner
            except User.DoesNotExist:
                owner_set = False

            if not (user.is_superuser and owner_set):
                self.owner = user
        super(OwnedObject, self).save(force_insert, force_update, using)
