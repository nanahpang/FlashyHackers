from django.contrib.auth.models import User
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

# Create your models here.

class Group(models.Model):
	name = models.CharField(max_length = 30, primary_key=True)
	admin = models.ForeignKey(User)

	def __str__(self):
		return self.name

class Membership(models.Model):
	member = models.ForeignKey(User)
	group = models.ForeignKey(Group)


class Message(models.Model):
	content = models.CharField(max_length = 140)
	DEFAULT = 'DF'
	GROUP_INVITATION = 'GI'
	MEETING_INVITATION = 'MI'
	NOTIFICATION = 'NO'
	MESSAGE_TYPES_CHOICES = (
        (NOTIFICATION, 'Notification'),
        (GROUP_INVITATION, 'Group_invitaion'),
        (MEETING_INVITATION, 'Meeting_invitation'),
        (DEFAULT, 'Default'),
    )
	messageType = models.CharField(max_length = 2, choices = MESSAGE_TYPES_CHOICES, default = DEFAULT)
	sender = models.ForeignKey(User, related_name = 'send_dm')
	recipient = models.ForeignKey(User, related_name = 'received_dm')
	sent_at = models.DateTimeField(null=True, blank=True)
	read_at = models.DateTimeField(null=True, blank=True)

	@property
	def read(self):
		if self.read_at is not None:
			return True
		return False

	def __str__(self):
		return self.content

	def save(self, **kwargs):
		if self.sender == self.recipient:
			raise ValidationError("You can't send messages to yourself")

		if not self.id:
			self.sent_at = timezone.now()
		super(Message, self).save(**kwargs)