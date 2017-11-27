from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from schedule.models import Event, Occurrence
from schedule.widgets import SpectrumColorPicker
from bootstrap3_datetime.widgets import DateTimePicker

class SpanForm(forms.ModelForm):
    # start = forms.SplitDateTimeField(label=_("start"))
    # end = forms.SplitDateTimeField(label=_("end"),
                                   # help_text=_("The end time must be later than start time."))
    start = forms.DateTimeField(label=_("start"),required=True,
                                 widget=DateTimePicker(options={"format": "MM/DD/YYYY HH:mm", "pickSeconds": False}))
    end = forms.DateTimeField(label=_("end"),required=True,
                               widget=DateTimePicker(options={"format": "MM/DD/YYYY HH:mm", "pickSeconds": False}),
                               help_text=_("The end time must be later than start time."))

    def clean(self):
        if 'end' in self.cleaned_data and 'start' in self.cleaned_data:
            if self.cleaned_data['end'] <= self.cleaned_data['start']:
                raise forms.ValidationError(_("The end time must be later than start time."))
        return self.cleaned_data


class EventForm(SpanForm):
    def __init__(self, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)

    end_recurring_period = forms.DateTimeField(label=_("End recurring period"),
                                               help_text=_("This date is ignored for one time only events."),
                                               required=False)

    class Meta(object):
        model = Event
        exclude = ('creator', 'created_on', 'calendar')
        widgets = {'start': forms.DateTimeInput(attrs={'class': 'datepicker'}),
                    'end': forms.DateTimeInput(attrs={'class': 'datepicker'})}


class OccurrenceForm(SpanForm):
    class Meta(object):
        model = Occurrence
        exclude = ('original_start', 'original_end', 'event', 'cancelled')



class EventAdminForm(forms.ModelForm):
    class Meta:
        exclude = []
        model = Event
        widgets = {
            'color_event': SpectrumColorPicker,
        }
