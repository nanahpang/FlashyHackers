#from django.utils.translation import ugettext_lazy as _
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from MS.models import Group
#from bootstrap3_datetime.widgets import DateTimePicker

class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    last_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    email = forms.EmailField(max_length=254, help_text='Required. Inform a valid email address.')

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', )


class CreatePartialGroupForm(forms.ModelForm):
    name = forms.CharField(label = 'Group Name:', max_length=30, help_text='*Required. Only alphabets and numbers accepted')
    #admin_name = forms.CharField(label = 'Admin Name:', max_length=30, help_text='*Required.')
    class Meta:
        model = Group
        exclude = ['admin']
'''
class SpanForm(forms.ModelForm):
     # start = forms.SplitDateTimeField(label=_("start"))
     # end = forms.SplitDateTimeField(label=_("end"),
                                    # help_text=_("The end time must be later than start time."))
     start = forms.DateTimeField(label=_("start"),required=True,
                                  widget=DateTimePicker(options={"format": "MM/DD/YYYY HH:mm", "pickSeconds": False}))
     end = forms.DateTimeField(label=_("end"),required=True,
                                widget=DateTimePicker(options={"format": "MM/DD/YYYY HH:mm", "pickSeconds": False}),
                                help_text=_("The end time must be later than start time."))
                 raise forms.ValidationError(_("The end time must be later than start time."))
         return self.cleaned_data


class EventForm(SpanForm):
     def __init__(self, *args, **kwargs):
         super(EventForm, self).__init__(*args, **kwargs)

     end_recurring_period = forms.DateTimeField(label=_("End recurring period"),
                                                help_text=_("This date is ignored for one time only events."),
                                                required=False)

     class Meta(object):
         #model = Event
         #exclude = ('creator', 'created_on', 'calendar')
         widgets = {'start': forms.DateTimeInput(attrs={'class': 'datepicker'}),
                     'end': forms.DateTimeInput(attrs={'class': 'datepicker'})}
'''
