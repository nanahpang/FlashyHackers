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
import simplejson as json
def signup(request):
    form = SignUpForm(request.POST)
    if form.is_valid():
        form.save()
        username = form.cleaned_data.get('username')
        raw_password = form.cleaned_data.get('password1')
        user = authenticate(username=username, password=raw_password)
        login(request, user)
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
            group.admin = request.user.username
            group.name = form.cleaned_data.get('group_name')
            #group = Group(group_name=groupname, admin_name = adminname)
            group.save()
            group = Group.objects.get(name =  name)
            member = User.objects.get(username = request.user.username)
            p = Membership(group = group, member = member)
            p.save()

            #alert("%s is created by %s" %(group.group_name, group.admin_name))
            messages.success(request,'%s is created by %s' %(group.name, group.admin))
            return redirect('home')
    else:
        form = CreatePartialGroupForm()
    #if request.method == 'GET':
    return render(request,'MS/creategroup.html',{'form': form})

def viewadmingroups(request):
    username = request.POST.get('username')
    admin_entries = Group.objects.filter(admin=username)
    user = User.objects.get(username = username)
    member_entries = Membership.objects.filter(member=user)
    admin_results = []
    member_results = []
    for item in admin_entries:
        data_json = item.name
        admin_results.append(data_json)
    for item in member_entries:
        data_json = item.group.name
        member_results.append(data_json)
    res = {'admin': admin_results, 'member':member_results}
    res = json.dumps(res)
    mimetype = 'application/json'
    return HttpResponse(res, mimetype)


def showgroup(request):
    group_name = request.POST.get('group_name')
    data = Membership.objects.filter(group = group_name)
    admin = Group.objects.get(name = group_name).admin
    results = []
    print(results)
    for item in data:
        data_json = item.group
        data_json = item.member.username
        results.append(data_json)
    res = {'admin' : admin, 'member' : results}
    print(res)
    res = json.dumps(res)
    mimetype = 'application/json'
    return HttpResponse(res, mimetype)

def addnewmember(request):
    group_name = request.POST.get('group_name')
    member_id = request.POST.get('memberid')
    group = Group.objects.get(name = group_name)
    member = User.objects.get(username = member_id)
    p = Membership(group = group, member = member)
    p.save()
    result = 'true'
    result = json.dumps(result)
    mimetype = 'application/json'
    return HttpResponse(result, mimetype)

#calendar management
def calendar(request):
    print("haha")
    return render(request, "MS/fullcalendar.html")




