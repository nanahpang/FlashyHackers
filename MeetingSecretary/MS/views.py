from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
# from oauth2client.contrib.django_orm import Storage
# from MS.models import CredentialsModel

# Create your views here.
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from MS.forms import SignUpForm, CreatePartialGroupForm
from MS.models import Group, Membership
from django.core import serializers

try: import simplejson as json
except ImportError: import json
from schedule.models.calendars import CalendarManager, Calendar
from django.utils import timezone
from .messageHandler import MessageHandler
messageHandler = MessageHandler()

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
            group.admin = request.user
            group.name = form.cleaned_data.get('name')
            group.save()
            group = Group.objects.get(name=group.name)
            member = User.objects.get(username=request.user.username)
            p = Membership(group=group, member=member)
            p.save()
            messages.success(request,'%s is created by %s' %(group.name, group.admin.username))
            return redirect('home')
    else:
        form = CreatePartialGroupForm()
    #if request.method == 'GET':
    return render(request,'MS/creategroup.html',{'form': form})

def viewadmingroups(request):
    username = request.POST.get('username')
    user = User.objects.get(username = username)
    admin_entries = Group.objects.filter(admin=user)
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
    admin = Group.objects.get(name = group_name).admin.username

    results = []
    for item in data:
        data_json = item.group
        data_json = item.member.username
        results.append(data_json)
    res = {'admin' : admin, 'member' : results}
    res = json.dumps(res)
    mimetype = 'application/json'
    return HttpResponse(res, mimetype)

def deletegroup(request):
    group_name = request.POST.get('groupid')
    operationuser = request.POST.get('operationuser')
    q = Group.objects.get(name = group_name)
    if q.admin.username == operationuser :
         p  = Membership.objects.filter(group = group_name)
         p.delete()
         q.delete()
         result = 'true'
    else :
         result = 'false'
    res = {'valid': result}
    res = json.dumps(res)
    mimetype = 'application/json'
    return HttpResponse(res, mimetype)


def addnewmember(request):
    group_name = request.POST.get('group_name')
    member_id = request.POST.get('memberid')
    group_admin = request.POST.get('group_admin')
    group = Group.objects.get(name = group_name)
    if group.admin.username == group_admin :
        from_user = group.admin
        member = User.objects.filter(username = member_id)
        if len(member) == 0:
            result = 'false'
        else:
            status = sendgroupinvitation(from_user, member[0], group)
            if status == True:
                result = 'true'
            else:
                result = 'false'
    else :
        result = 'false'
    res = {'valid': result}
    res = json.dumps(res)
    mimetype = 'application/json'
    return HttpResponse(res, mimetype)

def deletemember(request):
    group_name = request.POST.get('group_name')
    member_id = request.POST.get('memberid')
    operationuser = request.POST.get('operationuser')
    group = Group.objects.get(name = group_name)
    if group.admin.username == operationuser and member_id != operationuser:
        member = User.objects.get(username = member_id)
        p = Membership.objects.get(group = group_name, member = member)
        p.delete()
        result = 'true'
    else:
        result = 'false'
    res = {'valid': result}
    res = json.dumps(res)
    mimetype = 'application/json'
    return HttpResponse(res, mimetype)

def accept(request):
    group_name = request.POST.get('group_name')
    username = request.POST.get('username')
    member = User.objects.get(username = username)
    group = Group.objects.get(name = group_name)
    
    #let this new member join group
    p = Membership(group = group, member = member)
    p.save()
    result = 'true'
    
    #send notification to admin
    admin = Group.objects.get(name = group_name).admin
    message = username+ ' has accepted your invitation of joining group '+ group_name
    status = messageHandler.send_message(member, admin, message)
    
    #modify all other invitations related to this event 'accepted'
    messageHandler.set_invitation_accept(member, group)
    
    #return result to ajax
    res = {'valid': result}
    res = json.dumps(res)
    mimetype = 'application/json'
    return HttpResponse(res, mimetype)

def reject_group(request):
    group_name = request.POST.get('group_name')
    username = request.POST.get('username')
    member = User.objects.get(username = username)
    group = Group.objects.get(name = group_name)
     
    #send notification to admin
    admin = Group.objects.get(name = group_name).admin
    message = username+ ' has rejected your invitation of joining group '+ group_name
    status = messageHandler.send_message(member, admin, message)
    
    #modify all other invitations related to this event 'accepted'
    messageHandler.set_invitation_reject(member, group)
    result = 'true'
    #return result to ajax
    res = {'valid': result}
    res = json.dumps(res)
    mimetype = 'application/json'
    return HttpResponse(res, mimetype)

#for messages

def sendgroupinvitation(from_user, to_user, group):
    status = messageHandler.send_groupinvitation(from_user, to_user, group)
    if status == 200:
        result = True
    else:
        result = False
    return result


def view_notification(request):
    username = request.POST.get('username')
    user = User.objects.get(username = username)
    messages_entries = messageHandler.get_unread_message(user)
    messages = []
    for item in messages_entries:
        item.read_at = timezone.now()
        item.save()
        message = {
            'content' : item.content,
            'sent_at' : item.sent_at.isoformat()
        }
        messages.append(message)
    res = json.dumps(messages)
    mimetype = 'application/json'
    return HttpResponse(res, mimetype)

def view_groupinvitation(request):
    username = request.POST.get('username')
    user = User.objects.get(username = username)
    invitation_entries = messageHandler.get_invitation(user)
    invitations = []
    for item in invitation_entries:
        invitation = {
            'group':item.group.name,
            'admin': item.sender.username,
            'status' : item.status,
            'sent_at' : item.sent_at.isoformat()
        }
        invitations.append(invitation)
    res = json.dumps(invitations)
    mimetype = 'application/json'
    return HttpResponse(res, mimetype)


#calendar management
def calendar(request):
    return render(request, "MS/fullcalendar.html")
    # username = request.POST.get('username')
    # user = User.objects.get(username = username)
    # print(user.username)
    # url = "/schedule/fullcalendar/" + 'username' + "/"
    # print(url)
    # # return render(request,'./fullcalendar.html','calendar_slug'=username)
    # return HttpResponseRedirect(url)




