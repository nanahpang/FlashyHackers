from django.contrib.auth.models import User
from django.db import models
from django.contrib.auth.models import User

<<<<<<< HEAD

=======
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
>>>>>>> 91e88fda8420a77dd1feaa050b1a871f3dedce77
