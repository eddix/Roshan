from django.contrib.auth.models import User, check_password
from django.db import models

class Path(models.Model):
    users = models.ManyToManyField(User)
    path = models.CharField(max_length=512)
    perm = models.BooleanField()
    
    def __unicode__(self):
        if self.perm:
            return "[ALLOW] %s to (%s)"%(self.path, ', '.join(map(unicode, self.users.all())))
        else:
            return "[DENY] %s to (%s)"%(self.path, ', '.join(map(unicode, self.users.all())))
