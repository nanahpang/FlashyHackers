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


class Meeting(models.Model):
	group = models.ForeignKey(Group)
	title = models.CharField(max_length = 140)
	description = models.TextField(blank=True)
	start_time = models.DateTimeField()
	end_time = models.DateTimeField()

class GroupInvitation(models.Model):
	sender = models.ForeignKey(User, related_name = 'send_gi')
	recipient = models.ForeignKey(User, related_name = 'received_gi')
	group = models.ForeignKey(Group, related_name = 'group_gi')
	sent_at = models.DateTimeField(null=True, blank=True)
	ACCEPT = 'AC'
	REJECT = 'RJ'
	NORESPONSE = 'NO'
	STATUS_OF_MESSAGES_CHOICES = (
        (ACCEPT, 'Accepted'),
        (REJECT, 'Rejected'),
        (NORESPONSE, 'No response')
    )
	status = models.CharField(max_length = 2, choices = STATUS_OF_MESSAGES_CHOICES, default = NORESPONSE)

	def save(self, **kwargs):
		if not self.id:
			self.sent_at = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
		super(GroupInvitation, self).save(**kwargs)

class MeetingInvitation(models.Model):
	sender = models.ForeignKey(User, related_name = 'send_mi')
	recipient = models.ForeignKey(User, related_name = 'received_mi')
	group = models.ForeignKey(Group, related_name = 'group_mi')
	sent_at = models.DateTimeField(null=True, blank=True)
	meeting = models.ForeignKey(Meeting, related_name = 'mi')
	ACCEPT = 'AC'
	REJECT = 'RJ'
	NORESPONSE = 'NO'
	STATUS_OF_MESSAGES_CHOICES = (
        (ACCEPT, 'Accepted'),
        (REJECT, 'Rejected'),
        (NORESPONSE, 'No response')
    )
	status = models.CharField(max_length = 2, choices = STATUS_OF_MESSAGES_CHOICES, default = NORESPONSE)

	def save(self, **kwargs):
		if not self.id:
			self.sent_at = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
		super(MeetingInvitation, self).save(**kwargs)
class Message(models.Model):
	content = models.CharField(max_length = 140)
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