from django.contrib.auth.models import User
from django.db import models

# Create your models here.

class Group(models.Model):
	name = models.CharField(max_length = 30, primary_key=True)
	admin = models.CharField(max_length = 30)

	def __str__(self):
		return self.name

class Membership(models.Model):
	member = models.ForeignKey(User)
	group = models.ForeignKey(Group)
