import pytz
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
# Create your views here.
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from MS.forms import SignUpForm, CreatePartialGroupForm
from MS.models import Group, Membership
from django.utils import timezone
# Copy from schedule
from django.conf import settings
from django.db.models import Q
from django.http import (
    HttpResponseBadRequest, HttpResponseRedirect, JsonResponse,
)
from schedule.models import Calendar, Occurrence
try:
    import simplejson as json
except ImportError:
    import json
from .messageHandler import MessageHandler
msgHandler = MessageHandler()

def signup(request):
    """
    :param request: the request from user to sign-up a new account
    :return: render a html template with form entries
    """
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
    """
    :param request: request to change the information
    :param type: what kind of information is the user changing
    :return: render a html with changed form
    """
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
    """
    :param request: request to create a group
    :return: render a html with group creation information
    """
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
            messages.success(request, '%s is created by %s' %(group.name, group.admin.username))
            return redirect('home')
    else:
        form = CreatePartialGroupForm()
    #if request.method == 'GET':
    return render(request, 'MS/creategroup.html', {'form': form})

def viewadmingroups(request):
    """
    :param request: request to view groups as admin
    :return: HTTP response to the groups view
    """
    username = request.POST.get('username')
    user = User.objects.get(username=username)
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
    """
    :param request: request to show the groups that the user is in
    :return: HTTP response for all his groups
    """
    group_name = request.POST.get('group_name')
    data = Membership.objects.filter(group=group_name)
    admin = Group.objects.get(name=group_name).admin.username

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
    """
    :param request: request for a group deletion as admin
    :return: HTTP response for deletion
    """
    group_name = request.POST.get('groupid')
    operationuser = request.POST.get('operationuser')
    q = Group.objects.get(name=group_name)
    if q.admin.username == operationuser:
        p = Membership.objects.filter(group=group_name)
        p.delete()
        q.delete()
        result = 'true'
    else:
        result = 'false'
    res = {'valid': result}
    res = json.dumps(res)
    mimetype = 'application/json'
    return HttpResponse(res, mimetype)


def addnewmember(request):
    """
    :param request: request for adding a new group member to the group
    :return: HTTP response for the adding request
    """
    group_name = request.POST.get('group_name')
    member_id = request.POST.get('memberid')
    group_admin = request.POST.get('group_admin')
    group = Group.objects.get(name=group_name)
    if group.admin.username == group_admin:
        from_user = group.admin
        member = User.objects.filter(username=member_id)
        if len(member) == 0:
            result = 'false'
        else:
            status = sendgroupinvitation(from_user, member[0], group)
            if status == True:
                result = 'true'
            else:
                result = 'false'
    else:
        result = 'false'
    res = {'valid': result}
    res = json.dumps(res)
    mimetype = 'application/json'
    return HttpResponse(res, mimetype)

def deletemember(request):
    """
    :param request: request for deleting a group member
    :return: HTTP response for deletion
    """
    group_name = request.POST.get('group_name')
    member_id = request.POST.get('memberid')
    operationuser = request.POST.get('operationuser')
    group = Group.objects.get(name=group_name)
    if group.admin.username == operationuser and member_id != operationuser:
        member = User.objects.get(username=member_id)
        p = Membership.objects.get(group=group_name, member=member)
        p.delete()
        result = 'true'
    else:
        result = 'false'
    res = {'valid': result}
    res = json.dumps(res)
    mimetype = 'application/json'
    return HttpResponse(res, mimetype)

def accept(request):
    """
    :param request: posting request that accepts the invitation
    :return: HTTP response for accepting
    """
    group_name = request.POST.get('group_name')
    username = request.POST.get('username')
    member = User.objects.get(username=username)
    group = Group.objects.get(name=group_name)

    #let this new member join group
    p = Membership(group=group, member=member)
    p.save()
    result = 'true'
    
    #send notification to admin
    admin = Group.objects.get(name=group_name).admin
    message = username+ ' has accepted your invitation of joining group '+ group_name
    status = msgHandler.send_message(member, admin, message)

    #modify all other invitations related to this event 'accepted'
    msgHandler.set_invitation_accept(member, group)

    #return result to ajax
    res = {'valid': result}
    res = json.dumps(res)
    mimetype = 'application/json'
    return HttpResponse(res, mimetype)

def reject_group(request):
    """
    :param request: posting request that rejects the invitation
    :return: HTTP response for rejecting
    """
    group_name = request.POST.get('group_name')
    username = request.POST.get('username')
    member = User.objects.get(username=username)
    group = Group.objects.get(name=group_name)
     
    #send notification to admin
    admin = Group.objects.get(name=group_name).admin
    message = username+ ' has rejected your invitation of joining group '+ group_name
    status = msgHandler.send_message(member, admin, message)

    #modify all other invitations related to this event 'accepted'
    msgHandler.set_invitation_reject(member, group)
    result = 'true'
    #return result to ajax
    res = {'valid': result}
    res = json.dumps(res)
    mimetype = 'application/json'
    return HttpResponse(res, mimetype)

#for messages

def sendgroupinvitation(from_user, to_user, group):
    """
    :param from_user: the user that sends the invitation
    :param to_user: the user that receive the invitation
    :param group: the group that the from_user want the person to join in
    :return: the status if the msg has been sent
    """
    status = msgHandler.send_groupinvitation(from_user, to_user, group)
    if status == 200:
        result = True
    else:
        result = False
    return result


def view_notification(request):
    """
    :param request: posting request to view the notification
    :return: HTTP response for viewing
    """
    username = request.POST.get('username')
    user = User.objects.get(username=username)
    messages_entries = msgHandler.get_unread_message(user)
    messages_list = []
    for item in messages_entries:
        item.read_at = timezone.now()
        item.save()
        msg = {
            'content' : item.content,
            'sent_at' : item.sent_at.isoformat()
        }
        messages.append(msg)
    res = json.dumps(messages_list)
    mimetype = 'application/json'
    return HttpResponse(res, mimetype)

def view_groupinvitation(request):
    """
    :param request: request to view the group invitation from an admin
    :return: HTTP response for viewing the group invitation
    """
    username = request.POST.get('username')
    user = User.objects.get(username=username)
    invitation_entries = msgHandler.get_invitation(user)
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
    """
    :param request: request to access the personal calendar view
    :return: render a HTML template for the calendar
    """
    return render(request, "MS/fullcalendar.html")
    # username = request.POST.get('username')
    # user = User.objects.get(username = username)
    # print(user.username)
    # url = "/schedule/fullcalendar/" + 'username' + "/"
    # print(url)
    # # return render(request,'./fullcalendar.html','calendar_slug'=username)
    # return HttpResponseRedirect(url)
def groupcalendar(request):
    """
    :param request: admin's request to get the calendar for the whole group
    :return: render a HTML calendar with events of the whole group
    """
    return render(request, "MS/groupcalendar.html")

def api_group(request):
    """
    :param request: request to connect to the api that enables to generate the json for all group members
    :return: render a JsonResponse
    """
    start = request.GET.get('start')
    end = request.GET.get('end')
    timezone = request.GET.get('timezone')
    group_name = request.GET.get('group_name')
    data = Membership.objects.filter(group=group_name)
    results = []
    for item in data:
        data_json = item.member.username
        results.append(data_json)
    try:
        response_data = _api_group(start, end, results, timezone)
    except (ValueError, Calendar.DoesNotExist) as exp:
        return HttpResponseBadRequest(exp)
    return JsonResponse(response_data, safe=False)

def _api_group(start, end, calendar_slug, timezone):
    """
    :param start: start time of the event
    :param end: end time of the event
    :param calendar_slug: username
    :param timezone: timezone
    :return: response group data to api_group function
    """

    if not start or not end:
        raise ValueError('Start and end parameters are required')
    # version 2 of full calendar
    # TODO: improve this code with date util package
    if '-' in start:
        def convert(date_time):
            """
            :param date_time: datetime
            :return: formatted datetime
            """
            if date_time:
                datetime = date_time.split(' ')[0]
                return datetime.datetime.strptime(date_time, '%Y-%m-%d')
    else:
        def convert(datetime):
            """
            :param date_time: datetime
            :return: formatted datetime
            """
            return datetime.datetime.utcfromtimestamp(float(datetime))

    start = convert(start)
    end = convert(end)
    current_tz = False
    if timezone and timezone in pytz.common_timezones:
        # make start and end dates aware in given timezone
        current_tz = pytz.timezone(timezone)
        start = current_tz.localize(start, False)
        end = current_tz.localize(end, False)
    elif settings.USE_TZ:
        # If USE_TZ is True, make start and end dates aware in UTC timezone
        utc = pytz.UTC
        start = utc.localize(start, False)
        end = utc.localize(end, False)

    if calendar_slug:
        # will raise DoesNotExist exception if no match
        calendars = []
        for item in calendar_slug:
            calendars.append(Calendar.objects.get(slug=item))

        # calendars = [Calendar.objects.get(slug=calendar_slug)]
    # if no calendar slug is given, get all the calendars
    else:
        calendars = Calendar.objects.all()
    response_data = []
    # Algorithm to get an id for the occurrences in fullcalendar (NOT THE SAME
    # AS IN THE DB) which are always unique.
    # Fullcalendar thinks that all their "events" with the same "event.id" in
    # their system are the same object, because it's not really built around
    # the idea of events (generators)
    # and occurrences (their events).
    # Check the "persisted" boolean value that tells it whether to change the
    # event, using the "event_id" or the occurrence with the specified "id".
    # for more info https://github.com/llazzaro/django-scheduler/pull/169
    i = 1
    if Occurrence.objects.all().count() > 0:
        i = Occurrence.objects.latest('id').id + 1
    event_list = []
    for calendar in calendars:
        # create flat list of events from each calendar
        event_list += calendar.events.filter(start__lte=end).filter(
            Q(end_recurring_period__gte=start) |
            Q(end_recurring_period__isnull=True))
    for event in event_list:
        occurrences = event.get_occurrences(start, end)
        for occurrence in occurrences:
            occurrence_id = i + occurrence.event.id
            existed = False

            if occurrence.id:
                occurrence_id = occurrence.id
                existed = True

            recur_rule = occurrence.event.rule.name \
                if occurrence.event.rule else None

            if occurrence.event.end_recurring_period:
                recur_period_end = occurrence.event.end_recurring_period
                if current_tz:
                    # make recur_period_end aware in given timezone
                    recur_period_end = recur_period_end.astimezone(current_tz)
                recur_period_end = recur_period_end
            else:
                recur_period_end = None

            event_start = occurrence.start
            event_end = occurrence.end
            if current_tz:
                # make event start and end dates aware in given timezone
                event_start = event_start.astimezone(current_tz)
                event_end = event_end.astimezone(current_tz)

            response_data.append({
                'id': occurrence_id,
                'title': occurrence.title,
                'start': event_start,
                'end': event_end,
                'existed': existed,
                'event_id': occurrence.event.id,
                'color': occurrence.event.color_event,
                'description': occurrence.description,
                'rule': recur_rule,
                'end_recurring_period': recur_period_end,
                'creator': str(occurrence.event.creator),
                'calendar': occurrence.event.calendar.slug,
                'cancelled': occurrence.cancelled,
            })
    return response_data