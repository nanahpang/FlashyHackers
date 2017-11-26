from .models import Message
from django.core.exceptions import ValidationError

class MessageHandler():

    def __init__(self): 
        pass

    def send_message(self, sender, recipient, message, messageType) :

        if sender == recipient :
            ValidationError('You cannot send message to yourself.')

        message = Message(sender = sender, recipient = recipient, content = str(message), messageType = messageType)
        message.save()

        return 200

    def get_unread_message(self, user) :
        return Message.objects.all().filter(recipient = user, read_at=None)
