from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
# from oauth2client.contrib.django_orm import Storage
# from MS.models import CredentialsModel

# Create your views here.
from django.http import HttpResponse, JsonResponse
from MS.forms import SignUpForm, CreatePartialGroupForm
from MS.models import Group, Membership
from django.core import serializers
try: import simplejson as json
except ImportError: import json
from schedule.models.calendars import CalendarManager, Calendar


def signup(request):
    form = SignUpForm(request.POST)
    if form.is_valid():
        form.save()
        username = form.cleaned_data.get('username')
        raw_password = form.cleaned_data.get('password1')
        user = authenticate(username=username, password=raw_password)
        login(request, user)
        
        calendar = Calendar(name=username+"_cal", slug=username)
        calendar.save()
        calendar.create_relation(user)

        #print('is valid')
        return redirect('home')
    else:
        form = SignUpForm()
    #print('first time')
    return render(request, 'MS/signup.html', {'form': form})

def test(request):
    return render(request, 'MS/change.html')

def change(request, type):
    if request.method == 'GET':
        return render(request, 'MS/change.html', {'type': type})
    else:
        if type == "password":
            password1 = request.POST['first_password']
            password2 = request.POST['second_password']
            if password1 != password2:
                return render(request, 'MS/change.html', {'type': type, 'warn': 'password_diff'})
            elif password1 == '':
                return render(request, 'MS/change.html', {'type': type, 'warn': 'password_empty'})
            request.user.set_password(password1)
            request.user.save()
            user = authenticate(request, username=request.user.username, password=password1)
            login(request, user)
        elif type == "information":
            request.user.first_name = request.POST['first_name']
            request.user.last_name = request.POST['last_name']
            email = request.POST['email']
            if email == '':
                return render(request, 'MS/change.html', {'type': type, 'warn': 'email_empty'})
            request.user.email = email
            request.user.save()
    return render(request, 'MS/home.html', {'from_change': 'success'})

#group management part

def creategroup(request):
    if request.method == 'POST':
        form = CreatePartialGroupForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            #groupname = form.cleaned_data.get('groupname')
            group.admin_name = request.user.username
            group.group_name = form.cleaned_data.get('group_name')
            #group = Group(group_name=groupname, admin_name = adminname)
            group.save()
            #alert("%s is created by %s" %(group.group_name, group.admin_name))
            messages.success(request,'%s is created by %s' %(group.group_name, group.admin_name))
            return redirect('home')
    else:
        form = CreatePartialGroupForm()
    #if request.method == 'GET':
    return render(request,'MS/creategroup.html',{'form': form})

def viewgroups(request):
    if request.method == 'GET':
        all_entries = Group.objects.filter(admin_name=request.user.username)
        return render(request,'MS/viewgroups.html', {'data' : all_entries})


def showgroup(request):
    group_name = request.POST.get('group_name')
    print(group_name)
    data = Group.objects.filter(group_name = group_name)
    results = []
    for item in data:
        data_json = item.group_name
        data_json = item.admin_name
        results.append(data_json)
    res = json.dumps(results)
    mimetype = 'application/json'
    return HttpResponse(res, mimetype)

#calendar management
def calendar(request):
    return render(request, "MS/fullcalendar.html")




