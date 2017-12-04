"""MeetingSecretary URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from MS import views
from django.contrib.auth import views as auth_views
#from django.views.generic.base import TemplateView

from django.views.generic import TemplateView

from django.conf import settings
from schedule.views import CreateEventView


admin.autodiscover()


urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name='MS/home.html'), name='home'),
    url(r'^signup/', views.signup, name='signup'),
    url(r'^login/$', auth_views.login, {'template_name': 'MS/login.html'}, name='login'),
    url(r'^logout/$', auth_views.logout, {'template_name': 'MS/logged_out.html'}, name='logout'),
    url(r'^change/(?P<type>[a-z]+)/$', views.change, name='change'),
    url(r'^admin/', admin.site.urls),
    url(r'^creategroup/$', views.creategroup, name='creategroup'),
    url(r'^calendar/.*', TemplateView.as_view(template_name='MS/fullcalendar.html'),
        name='calendar'),
    url(r'^create_event/(?P<calendar_slug>[-\w]+)/$',
        CreateEventView.as_view(template_name='MS/create_event.html'),
        name='calendar_create_event'),
    url(r'^groupcalendar/', views.api_group, name='api_group'),
    url(r'^viewallgroups/', TemplateView.as_view(template_name='MS/viewallgroups.html'),
        name='viewallgroups'),
    url(r'^ajax/viewadmingroups/$', views.viewadmingroups, name='viewadmingroups'),
    url(r'^ajax/showgroup/', views.showgroup, name='showgroup'),
    url(r'^groups/(?P<group_name>([0-9a-zA-Z_]*))/$', views.showonegroupfunc, name='groups'),
    url(r'^ajax/addnewmember/', views.addnewmember, name='addnewmember'),
    url(r'^ajax/deletemember/', views.deletemember, name='deletemember'),
    url(r'^ajax/deletegroup/', views.deletegroup, name='deletegroup'),
    url(r'^ajax/accept/', views.accept, name='accept'),
    url(r'^ajax/rejectgroup/', views.reject_group, name='reject_group'),
    url(r'^schedule/', include('schedule.urls'), name='scheduler'),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
    # to INSTALLED_APPS to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    #for messages
    url(r'^inbox/', TemplateView.as_view(template_name='MS/inbox.html')),
    url(r'^ajax/viewnotification/', views.view_notification, name='view_notification'),
    url(r'^ajax/viewgroupinvitation', views.view_groupinvitation, name='view_groupinvitation'),
    url(r'^profile/', TemplateView.as_view(template_name='MS/profile_page.html')),
    # Uncomment the next line to enable the admin:
    #for meeting
    url(r'^ajax/searchtime/', views.searchtime, name='searchtime'),
    url(r'^ajax/find_time/', views.find_time, name='find_time'),
    url(r'^ajax/addmeeting/', views.add_meeting, name='add_meeting'),
    url(r'^ajax/viewmeetinginvitation/', views.view_meetinginvitation,
        name='view_meetinginvitation'),
    url(r'^ajax/acceptmeeting/', views.accept_meeting, name='accept_meeting'),
    url(r'^ajax/rejectmeeting/', views.reject_meeting, name='reject_meeting'),
    url(r'^ajax/showmeeting/', views.show_meetings, name='show_meetings'),
    url(r'^ajax/changemeeting/', views.change_meeting, name='change_meeting'),
    url(r'^ajax/deletemeeting/', views.delete_meeting, name='delete_meeting'),
]
#if settings.DEBUG:
#    import debug_toolbar
#    urlpatterns += [
#        url(r'^__debug__/', include(debug_toolbar.urls)),
#    ]
