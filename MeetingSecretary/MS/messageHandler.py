from .models import Message, GroupInvitation
from django.core.exceptions import ValidationError

class MessageHandler():

    def __init__(self): 
        pass

    def send_message(self, sender, recipient, message) :

        if sender == recipient :
            ValidationError('You cannot send message to yourself.')

        message = Message(sender = sender, recipient = recipient, content = str(message))
        message.save()

        return 200

    def get_unread_message(self, user) :
        return Message.objects.all().filter(recipient = user, read_at=None)

    def send_groupinvitation(self, sender, recipient, group) :
        if sender == recipient:
            ValidationError('You cannot send message to yourself.')

        groupinvitation = GroupInvitation(sender = sender, recipient = recipient, group = group, status = 'NO')
        print(groupinvitation.sender.username)
        groupinvitation.save()

        return 200

    def get_invitation(self, user) :
        return GroupInvitation.objects.all().filter(recipient = user) 

    def set_invitation_accept(self, user, group):
        invitation_entries = GroupInvitation.objects.all().filter(recipient = user, group = group) 
        for item in invitation_entries:
            item.status = 'AC'
            item.save()
        return True

    def set_invitation_reject(self, user, group):
        invitation_entries = GroupInvitation.objects.all().filter(recipient = user, group = group) 
        for item in invitation_entries:
            item.status = 'RJ'
            item.save()
        return True
