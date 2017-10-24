from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Group(models.Model):
	group_name = models.CharField(max_length = 30)
	admin_name = models.CharField(max_length = 30)
	members = models.ManyToManyField(User, through = 'Membership')

	def __str__(self):
		return self.group_name

class Membership(models.Model):
	user = models.ForeignKey(User)
	group = models.ForeignKey(Group)
	date_joined = models.DateField()