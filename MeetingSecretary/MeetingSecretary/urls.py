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
from django.views.generic.base import TemplateView

from django.views.generic import TemplateView
from django.conf.urls import include, url

from django.conf import settings


admin.autodiscover()


urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name='MS/home.html'), name='home'),
    url(r'^signup/', views.signup, name='signup'),
    url(r'^login/$', auth_views.login, {'template_name': 'MS/login.html'}, name='login'),
    url(r'^logout/$', auth_views.logout, {'template_name': 'MS/logged_out.html'}, name='logout'),
    url(r'^change/(?P<type>[a-z]+)/$', views.change, name='change'),
    url(r'^admin/', admin.site.urls),
    url(r'^test/$', views.test, name='test'),
    url(r'^creategroup/$', views.creategroup, name='creategroup'),
    url(r'^calendar/$', views.calendar, name='calendar'),
    url(r'^viewallgroups/', TemplateView.as_view(template_name='MS/viewallgroups.html'), name='viewallgroups'),
    url(r'^ajax/viewadmingroups/$',views.viewadmingroups, name='viewadmingroups'),
    url(r'^ajax/showgroup/', views.showgroup, name='showgroup'),
    url(r'^groups/([a-z]*)', TemplateView.as_view(template_name='MS/groups.html'), name='groups'),
    url(r'^ajax/addnewmember/', views.addnewmember, name='addnewmember'),
    #url(r'^mygroups/$', views.mygroups, name='mygroups'),
    # url(r'^fullcalendar/', TemplateView.as_view(template_name="Calendar/fullcalendar.html"), name='fullcalendar'),
    url(r'^schedule/', include('schedule.urls'), name='scheduler'),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
    # to INSTALLED_APPS to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    #url(r'^admin/', include(admin.site.urls)),
]
#if settings.DEBUG:
#    import debug_toolbar
#    urlpatterns += [
#        url(r'^__debug__/', include(debug_toolbar.urls)),
#    ]
