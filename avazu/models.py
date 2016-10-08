from django.db import models

# Create your models here.

class RegisterUser(models.Model):
    username = models.CharField(max_length=50)
    name =  models.CharField(max_length=50)
    password = models.CharField(max_length=30)
    hosts = models.CharField(max_length=500)
    email = models.EmailField(max_length=50)
    expire_date = models.DateTimeField()
    is_added = models.SmallIntegerField(default=0)
  
    def __unicode__(self):
        return '%s(%s):%s' % (self.username, self.name,  self.email)

