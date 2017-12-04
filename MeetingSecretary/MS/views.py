import datetime
import pytz
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound
from django.http import HttpResponseBadRequest
from django.db.models import Q
from MS.forms import SignUpForm, CreatePartialGroupForm
from MS.models import Group, Membership, Meeting, MeetingEventRelationship
from schedule.models import Event, Occurrence
from schedule.models.calendars import Calendar
from .messageHandler import MessageHandler

try:
    import simplejson as json
except ImportError:
    import json
messageHandler = MessageHandler()

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
        return redirect('home')
    else:
        form = SignUpForm()
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
            user = authenticate(username=request.user.username, password=password1)
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
            membership = Membership(group=group, member=member)
            membership.save()
            messages.success(request, '%s is created by %s' %(group.name, group.admin.username))
            return redirect('home')
    else:
        form = CreatePartialGroupForm()
    return render(request, 'MS/creategroup.html', {'form': form})

def viewadmingroups(request):
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

def find_all_members(group, keepadmin):
    data = Membership.objects.filter(group=group)
    result = []
    if keepadmin is True:
        for item in data:
            result.append(item.member)
        return result
    result = []
    admin = Group.objects.get(name=group.name).admin
    for item in data:
        if item.member != admin:
            result.append(item.member)
    return result



def showgroup(request):
    group_name = request.POST.get('group_name')
    data = Membership.objects.filter(group=group_name)
    admin = Group.objects.get(name=group_name).admin.username

    results = []
    for item in data:
        data_json = item.member.username
        results.append(data_json)
    res = {'admin' : admin, 'member' : results}
    res = json.dumps(res)
    mimetype = 'application/json'
    return HttpResponse(res, mimetype)

def showonegroupfunc(request, group_name):
    print("come here")
    if group_name == '':
        return HttpResponseNotFound('<h1>No Page Here</h1>')
    group = Group.objects.filter(name=group_name)
    if len(group) == 0:
        return HttpResponseNotFound('<h1>No Page Here</h1>')
    if group[0].admin != request.user:
        return render(request, 'MS/groups.html', {'is_admin': 0})
    return render(request, 'MS/groups.html', {'is_admin': 1})




def deletegroup(request):
    """
    :param request: request for a group deletion as admin
    :return: HTTP response for deletion
    """
    group_name = request.POST.get('groupid')
    operationuser = request.POST.get('operationuser')
    groups = Group.objects.filter(name=group_name)
    if len(groups) != 0:
        if groups[0].admin.username == operationuser:
            admin = User.objects.get(username=operationuser)
            delete_notification = "The group " + group_name + " is removed\n"
            memberships = Membership.objects.filter(group=groups[0])
            # send notifications
            for membership in memberships:
                member = membership.member
                if member == admin:
                    continue
                messageHandler.send_message(admin, member, delete_notification)
                _deletememberfromgroup(group_name, member)
            _deletemeetings(groups[0])
            groups[0].delete()
            result = 'true'
        else:
            result = 'false-noright'
    else:
        result = 'false-nogroup'
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
            result = 'false-nomember'
        elif member[0] == group.admin:
            result = 'false-self'
        else:
            status = sendgroupinvitation(from_user, member[0], group)
            if status is True:
                result = 'true'
            else:
                result = 'false'
    else:
        result = 'false-noright'
    res = {'valid': result}
    res = json.dumps(res)
    mimetype = 'application/json'
    return HttpResponse(res, mimetype)

def deletemember(request):
    group_name = request.POST.get('group_name')
    member_id = request.POST.get('memberid')
    operationuser = request.POST.get('operationuser')
    group = Group.objects.get(name=group_name)
    if group.admin.username == operationuser and member_id != operationuser:
        member = User.objects.filter(username=member_id)
        if len(member) == 0:
            result = 'false-nomember'
        else:
            result = _deletememberfromgroup(group_name, member[0])
    elif group.admin.username != operationuser:
        result = 'false-noright'
    else:
        result = 'false-self'
    res = {'valid': result}
    res = json.dumps(res)
    mimetype = 'application/json'
    return HttpResponse(res, mimetype)


def _deletememberfromgroup(group_name, member):
    membership = Membership.objects.filter(group=group_name, member=member)
    if len(membership) == 0:
        result = 'false-nomember'
    else:
        meetings = Meeting.objects.filter(group=group_name)
        group = Group.objects.get(name=group_name)
        message = "You are removed from group " + group_name + '\n'
        messageHandler.send_message(group.admin, member, message)
        for meeting in meetings:
            _deletememberfrommeeting(meeting, member)
        membership[0].delete()
        result = 'true'
    return result

def _deletememberfrommeeting(meeting, member):
    events = Event.objects.filter(creator=member)
    message = "You are removed from meeting " + meeting.title + '\n'
    messageHandler.send_message(meeting.group.admin, member, message)
    for event in events:
        mers = MeetingEventRelationship.objects.filter(meeting=meeting, event=event)
        for mer in mers:
            mer.delete()

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
    membership = Membership.objects.filter(group=group, member=member)
    if len(membership) == 0:
        membership = Membership(group=group, member=member)
        membership.save()
        result = 'true'
    else:
        result = 'false'

    #send notification to admin
    admin = Group.objects.get(name=group_name).admin
    message = username+ ' has accepted your invitation of joining group '+ group_name
    messageHandler.send_message(member, admin, message)

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
    member = User.objects.get(username=username)
    group = Group.objects.get(name=group_name)

    #send notification to admin
    admin = Group.objects.get(name=group_name).admin
    message = username+ ' has rejected your invitation of joining group '+ group_name
    messageHandler.send_message(member, admin, message)

    #modify all other invitations related to this event 'accepted'
    messageHandler.set_invitation_reject(member, group)
    result = 'true'
    #return result to ajax
    res = {'valid': result}
    res = json.dumps(res)
    mimetype = 'application/json'
    return HttpResponse(res, mimetype)


#meeting management
def add_meeting(request):
    group_name = request.POST.get('group_name')
    title = request.POST.get('title')
    description = request.POST.get('description')
    start_time = request.POST.get('start_time')
    end_time = request.POST.get('end_time')
    group = Group.objects.get(name=group_name)
    admin = group.admin
    #find time convertor
    ##save this meeting into meeting table
    meeting = Meeting(group=group, title=title,
                      description=description, start_time=start_time, end_time=end_time)
    meeting.save()
    #bai! save event for the admin
    event = Event(title=title, description=description, start=start_time, end=end_time)
    event.creator = admin
    calendar = Calendar.objects.get(slug=admin.username)
    event.calendar = calendar
    event.save()
    #bai! save meetingeventrelationship for admin
    mer = MeetingEventRelationship(meeting=meeting, event=event)
    mer.save()

    ##send invitation to all member
    ###find all member
    memberlist = find_all_members(group, True)
    result = 'false'
    for member in memberlist:
        if member == admin:
            continue
        status = sendmeetinginvitation(admin, member, group, meeting)
        if status == True:
            result = 'true'
        else:
            result = 'false'
    data = {'valid': result}
    data = json.dumps(data)
    mimetype = 'application/json'
    return HttpResponse(data, mimetype)


def show_meetings(request):
    group_name = request.POST.get('group_name')
    group = Group.objects.get(name=group_name)
    meeting_list = Meeting.objects.all().filter(group=group)
    result = []
    for item in meeting_list:

        # bai!
        allmeetingrelationship = MeetingEventRelationship.objects.filter(meeting=item)
        meetingmembers = []
        for mer in allmeetingrelationship:
            event = mer.event
            user = User.objects.get(username=event.creator.username)
            meetingmembers.append(user.username)

        res = {
            'id' : item.id,
            'title' : item.title,
            'description' : item.description,
            'start_time' : item.start_time.isoformat(),
            'end_time' : item.end_time.isoformat(),
            'meetingmembers': meetingmembers
        }
        result.append(res)
    data = json.dumps(result)
    mimetype = 'application/json'
    return HttpResponse(data, mimetype)

def view_meetinginvitation(request):
    username = request.POST.get('username')
    user = User.objects.get(username=username)
    invitation_entries = messageHandler.get_meetinginvitation(user)
    invitations = []
    for item in invitation_entries:
        invitation = {
            'group':item.group.name,
            'admin': item.sender.username,
            'status' : item.status,
            'meeting' : {
                'id' : item.meeting.id,
                'group': item.meeting.group.name,
                'title': item.meeting.title,
                'start_time': item.meeting.start_time.isoformat(),
                'end_time': item.meeting.end_time.isoformat(),
                'description': item.meeting.description,
            },
            'sent_at' : item.sent_at.isoformat()
        }
        invitations.append(invitation)
    res = json.dumps(invitations)
    mimetype = 'application/json'
    return HttpResponse(res, mimetype)
#meeting_info(title, group, id)
def reject_meeting(request):
    meeting_info = request.POST.getlist('meeting_info[]')
    username = request.POST.get('username')
    group_name = meeting_info[1]
    title = meeting_info[0]
    meetingid = meeting_info[2]
    group = Group.objects.get(name=group_name)
    #send notification to admin
    admin = Group.objects.get(name=group_name).admin
    member = User.objects.get(username=username)
    message = username+ ' will not attend the meeting ' + title + 'of group ' + group_name + '.'
    status = messageHandler.send_message(member, admin, message)
    if status == 200:
        result = 'true'
    else:
        result = 'false'
    meeting = Meeting.objects.get(id=meetingid)
    messageHandler.set_meetinginvitation_reject(member, group, meeting)

    res = {'valid': result}
    res = json.dumps(res)
    mimetype = 'application/json'
    return HttpResponse(res, mimetype)


#meeting_info[title, description, group, start_time, end_time]
def accept_meeting(request):
    meeting_info = request.POST.getlist('meeting_info[]')
    username = request.POST.get('username')
    group_name = meeting_info[2]
    title = meeting_info[0]
    description = meeting_info[1]
    start_time = meeting_info[3]
    end_time = meeting_info[4]
    meetingid = meeting_info[5]

    # judge whether the member is in the meeting already
    meeting = Meeting.objects.get(id=meetingid)
    mers = MeetingEventRelationship.objects.filter(meeting=meeting)
    result = 'false'
    for mer in mers:
        if mer.event.creator.username == username:
            result = 'true'
            break

    if result == 'false':
        group = Group.objects.get(name=group_name)
        #send notification to admin
        admin = Group.objects.get(name=group_name).admin
        member = User.objects.get(username=username)
        message = username+ ' will attend the meeting ' + title + 'of group ' + group_name + '.'
        status = messageHandler.send_message(member, admin, message)
        if status == 200:
            result = 'true'
        else:
            result = 'false'
        if '-' in start_time:
            def convert(ddatetime):
                if ddatetime:
                    # ddatetime = ddatetime.split(' ')[0]
                    ddatetime = ddatetime.split('+')[0]
                    print("ddatetime is " + ddatetime)
                    time = datetime.datetime.strptime(ddatetime, '%Y-%m-%dT%H:%M:%S')
                    return time
        else:
            def convert(ddatetime):
                return datetime.datetime.utcfromtimestamp(float(ddatetime))

        #store an event of that user
        ##add event
        start_time = convert(start_time)
        end_time = convert(end_time)
        if settings.USE_TZ:
        # If USE_TZ is True, make start and end dates aware in UTC timezone
            utc = pytz.UTC
            start_time = utc.localize(start_time)
            end_time = utc.localize(end_time)
        event = Event(title=title, description=description, start=start_time, end=end_time)
        user = User.objects.get(username=username)
        calendar = Calendar.objects.get(slug=username)
        event.creator = user
        event.calendar = calendar
        event.save()

        # accept the invitation
        messageHandler.set_meetinginvitation_accept(member, group, meeting)
        #increase attendees

        # add meeting event relationship
        mer = MeetingEventRelationship(meeting=meeting, event=event)
        mer.save()
    res = {'valid': result}
    res = json.dumps(res)
    mimetype = 'application/json'
    return HttpResponse(res, mimetype)

def delete_meeting(request):
    meetingid = request.POST.get('id')
    meeting = Meeting.objects.get(id=meetingid)
    _deletemeeting(meeting)
    data = {'valid': 'true'}
    data = json.dumps(data)
    mimetype = 'application/json'
    return HttpResponse(data, mimetype)


def change_meeting(request):
    #print("come here")
    meetingid = request.POST.get('id')
    meeting = Meeting.objects.get(id=meetingid)
    # delete original meeting event relationship and events
    #mres = MeetingEventRelationship.objects.filter(meeting=meeting)
    #for mre in mres:
     #   event = mre.event
     #   event.delete()
     #   mre.delete()
    description = "Notice! Meeting information is changed !! Please decide whether  \
                you will attend again!! (original meeting event is deleted automatically)\n"

    _deletemeeting(meeting)
    group_name = request.POST.get('group_name')
    group = Group.objects.get(name=group_name)
    admin = group.admin
    title = request.POST.get('changed_title')
    description += request.POST.get('changed_description')
    start_time = request.POST.get('changed_start_time')
    end_time = request.POST.get('changed_end_time')

    meeting = Meeting(group=group, title=title, description=description,
                      start_time=start_time, end_time=end_time)
    meeting.save()

    event = Event(title=meeting.title,
                  description=meeting.description, start=meeting.start_time, end=meeting.end_time)
    event.creator = admin
    calendar = Calendar.objects.get(slug=admin.username)
    event.calendar = calendar
    event.save()
    mer = MeetingEventRelationship(meeting=meeting, event=event)
    mer.save()

    memberlist = find_all_members(group, True)
    result = 'true'
    for member in memberlist:
        if member == admin:
            continue
        status = sendmeetinginvitation(admin, member, group, meeting)
        if status is False:
            result = 'false'
    data = {'valid': result}
    data = json.dumps(data)
    mimetype = 'application/json'
    return HttpResponse(data, mimetype)



#for messages
def sendgroupinvitation(from_user, to_user, group):
    """
    :param from_user: the user that sends the invitation
    :param to_user: the user that receive the invitation
    :param group: the group that the from_user want the person to join in
    :return: the status if the msg has been sent
    """
    status = messageHandler.send_groupinvitation(from_user, to_user, group)
    result = bool(status == 200)
    return result

def sendmeetinginvitation(from_user, to_user, group, meeting):
    status = messageHandler.send_meetinginvitation(from_user, to_user, group, meeting)
    result = bool(status == 200)
    return result


def view_notification(request):
    """
    :param request: posting request to view the notification
    :return: HTTP response for viewing
    """
    username = request.POST.get('username')
    user = User.objects.get(username=username)
    messages_entries = messageHandler.get_unread_message(user)
    messages_list = []
    for item in messages_entries:
        item.read_at = timezone.now()
        item.save()
        msg = {
            'content' : item.content,
            'sent_at' : item.sent_at.isoformat()
        }
        messages_list.append(msg)
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
    invitation_entries = messageHandler.get_groupinvitation(user)
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


#test search available time
#def searchtime(request):
    #group_name = request.POST.get("group_name")
    #start_time = request.POST.get("start_time")
    #end_time = request.POST.get("end_time")
 #   res = []
    #for i in range(2):
 #   start = timezone.now().isoformat()
 #   end = timezone.now().isoformat()
 #   slot = []
 #   slot.append(start)
 #   slot.append(end)
 #   res.append(slot)
 #   result = {'slots' : res}
 #   result = json.dumps(result)
 #   mimetype = 'application/json'
 #   return HttpResponse(result, mimetype)

class Interval:
    def __init__(self, s=0, e=0):
        self.start = s
        self.end = e

def find_time(request):
    start = request.POST.get('start_time')
    end = request.POST.get('end_time')
    group_name = request.GET.get('group_name')
    timezone = request.GET.get('timezone')
    #timezone = 'US/Eastern'
    member_object = Membership.objects.filter(group=group_name)
    members = []
    response_data = []
    for item in member_object:
        data_json = item.member.username
        members.append(data_json)
    if not start or not end:
        raise ValueError('Start and end parameters are required')
    # version 2 of full calendar
    if '-' in start:
        def convert(ddatetime):
            if ddatetime:
                ddatetime = ddatetime.split(' ')[0]
                return datetime.datetime.strptime(ddatetime, '%Y-%m-%d')
    else:
        def convert(ddatetime):
            return datetime.datetime.utcfromtimestamp(float(ddatetime))

    #if '-' in start:
    #    def convert(ddatetime):
    #        if ddatetime:
    #            ddatetime = ddatetime.split(' ')[0]
    #            # print(ddatetime)\
    #            ddatetime = ddatetime.split('+')[0]
    #            return datetime.datetime.strptime(ddatetime, '%Y-%m-%dT%H:%M:%S')
    #else:
    #    def convert(ddatetime):
    #        return datetime.datetime.utcfromtimestamp(float(ddatetime))
    start = convert(start)
    end = convert(end)
    current_tz = False
    if timezone and timezone in pytz.common_timezones:
        # make start and end dates aware in given timezone
        current_tz = pytz.timezone(timezone)
        start = current_tz.localize(start)
        end = current_tz.localize(end)
    elif settings.USE_TZ:
        # If USE_TZ is True, make start and end dates aware in UTC timezone
        utc = pytz.UTC
        start = utc.localize(start)
        end = utc.localize(end)
    if members:
        # will raise DoesNotExist exception if no match
        calendars = []
        for item in members:
            calendars.append(Calendar.objects.get(slug=item))

        # calendars = [Calendar.objects.get(slug=calendar_slug)]
    # if no calendar slug is given, get all the calendars
    else:
        calendars = Calendar.objects.all()
    event_list = []
    # i = 1
    # if Occurrence.objects.all().count() > 0:
    #     i = Occurrence.objects.latest('id').id + 1
    for calendar in calendars:
        # create flat list of events from each calendar
        event_list += calendar.events.filter(start__lte=end).filter(
            Q(end_recurring_period__gte=start) |
            Q(end_recurring_period__isnull=True))
    intervals = []
    for event in event_list:
        occurrences = event.get_occurrences(start, end)
        for occurrence in occurrences:
            event_start = occurrence.start
            event_end = occurrence.end
            if current_tz:
                # make event start and end dates aware in given timezone
                event_start = event_start.astimezone(current_tz)
                event_end = event_end.astimezone(current_tz)
            interval = Interval(event_start, event_end)
            intervals.append(interval)

    intervals.sort(key=lambda x: x.start)
    length = len(intervals)
    res = []
    for i in range(length):
        if res == []:
            res.append(intervals[i])
        else:
            size = len(res)
            if res[size-1].start <= intervals[i].start <= res[size-1].end:
                res[size-1].end = max(intervals[i].end, res[size-1].end)
            else:
                res.append(intervals[i])
    if len(res) == 0:
        response_data.append([start, end])
        data = {'slots': response_data}
        return JsonResponse(data, safe=False)

    result = []
    for item in res:
        temp = [item.start, item.end]
        result.append(temp)
    length_r = len(result)
    response_data = []


    for i in range(length_r+1):
        if i == 0:
            if start >= res[i].start:
                continue
            else:
                res_start = start
                res_end = res[i].start

        elif i == length_r:
            if end <= res[i-1].end:
                continue
            else:
                res_start = res[i-1].end
                res_end = end
        else:
            res_start = res[i-1].end
            res_end = res[i].start
        response_data.append([res_start.isoformat(), res_end.isoformat()])
    data = {'slots': response_data}
    return JsonResponse(data, safe=False)

def _deletemeetings(group):
    meetings = Meeting.objects.filter(group=group)
    for meeting in meetings:
        _deletemeeting(meeting)
    return

def _deletemeeting(meeting):
    mers = MeetingEventRelationship.objects.filter(meeting=meeting)
    message = "Meeting " + meeting.title + " is deleted\n"
    if len(mers) == 0:
        return
    for mer in mers:
        if mer.event.creator != meeting.group.admin:
            status = messageHandler.send_message(meeting.group.admin, mer.event.creator, message)
        event = mer.event
        event.delete()
        mer.delete()
    # notice!! should send a message to members to notice
    meeting.delete()


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
    :param request: request to connect to the api that enables to generate
    :the json for all group members
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
    #if '-' in start:
    #    def convert(datetime):
    #        """
    #        :param datetime: datetime
    #        :return: formatted datetime
    #        """
    #        if datetime:
    #            datetime = datetime.split(' ')[0]
    #            return datetime.datetime.strptime(datetime, '%Y-%m-%d')
    #else:
    #    def convert(datetime):
    #        """
    #        :param datetime: datetime
    #        :return: formatted datetime
    #        """
    #        return datetime.datetime.utcfromtimestamp(float(datetime))

    if '-' in start:
        def convert(ddatetime):
            if ddatetime:
                ddatetime = ddatetime.split(' ')[0]
                return datetime.datetime.strptime(ddatetime, '%Y-%m-%d')
    else:
        def convert(ddatetime):
            return datetime.datetime.utcfromtimestamp(float(ddatetime))
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
