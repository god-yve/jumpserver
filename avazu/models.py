from django.db import models

# Create your models here.

class RegisterUser(models.Model):
    username = models.CharField(max_length=50)
    name =  models.CharField(max_length=50)
    password = models.CharField(max_length=30)
    hosts = models.CharField(max_length=2500)
    email = models.EmailField(max_length=50)
    expire_date = models.DateTimeField()
    #registered_date = models.DateTimeField(auto_now_add=True)
    is_added = models.SmallIntegerField(default=0)
  
    def __unicode__(self):
        return '%s(%s):%s' % (self.username, self.name,  self.email)


class ApplyHosts(models.Model):
    username = models.CharField(max_length=50)
    hosts =  models.CharField(max_length=2500)
    applied_date = models.DateTimeField(auto_now_add=True)
    is_added = models.SmallIntegerField(default=0)

