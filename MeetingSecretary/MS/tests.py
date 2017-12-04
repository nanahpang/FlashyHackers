import json
import codecs
from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from MS.models import Group, Membership, Meeting
from MS.models import GroupInvitation, MeetingEventRelationship, MeetingInvitation, Message
from MS import views
from MS.forms import SignUpForm, CreatePartialGroupForm
from django.core.urlresolvers import reverse
from schedule.models import Calendar, Event
from .messageHandler import MessageHandler
import datetime
messageHandler = MessageHandler()

# Create your tests here.
class PersonalProfileTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.User1 = User.objects.create_user(username="User1", first_name="first1"
                                              , last_name="last1", email="useremail1@server.com"
                                              , password="password1")
        self.User2 = User.objects.create_user(username="User2", first_name="first2"
                                              , last_name="last2", email="useremail2@server.com"
                                              , password="password2")

    def test_signup(self):
        post1 = {"username": "TestUser1", "first_name": "FN1", "last_name": "LN1",
                 "email": "email1@server.com", "password1": "passwordtest",
                 "password2": "passwordtest"}
        # two passwords are different
        post2 = {"username": "TestUser2", "first_name": "FN2", "last_name": "LN2",
                 "email": "email2@server.com", "password1": "passwordtest",
                 "password2": "passwordtest2"}
        # required information has to be filled
        post3 = {"username": "TestUser3", "first_name": "FN3", "last_name": "LN3",
                 "email": "", "password1": "passwordtest", "password2": "passwordtest"}
        response = self.client.post(reverse("signup"), post1)
        self.assertEqual(response.status_code, 302)
        response = self.client.post(reverse("signup"), post2)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse("signup"), post3)
        self.assertEqual(response.status_code, 200)
        Testuser1 = User.objects.get(username="TestUser1")
        Testuser2 = User.objects.filter(username="TestUser2")
        TestUser3 = User.objects.filter(username="TestUser3")
        self.assertEqual(Testuser1.first_name, "FN1")
        self.assertEqual(Testuser1.email, "email1@server.com")
        # Test password hash
        self.assertNotEqual(Testuser1.password, "passwordtest")
        self.assertEqual(len(Testuser2), 0)
        self.assertEqual(len(TestUser3), 0)

    def test_login(self):
        login = self.client.login(username="User1", password="password1")
        self.assertEqual(login, True)
        login = self.client.login(username="User1", password="password2")
        self.assertEqual(login, False)
        login = self.client.login(username="User3", password="password3")
        self.assertEqual(login, False)

    def test_logout(self):
        response = self.client.post(reverse("logout"))
        data = response.content.decode("utf-8")
        self.assertTrue("successfully logged out" in data)


    def test_change(self):
        login = self.client.login(username="User1", password="password1")
        post1 = {"first_password": "change", "second_password": "change"}
        post2 = {"first_name": "changefirst", "last_name": "changesecond", "email": "changeemail"}
        # two password are different
        post3 = {"first_password": "change", "second_password": "change2"}
        # password is empty
        post4 = {"first_password": "", "second_password": ""}
        # one required information is empty
        post5 = {"first_name": "changefirst", "last_name": "changesecond", "email": ""}

        response = self.client.post(reverse("change", kwargs={"type": "password"}), post1)
        data = response.content.decode('utf-8')
        self.assertTrue("Change success" in data)

        response = self.client.post(reverse("change", kwargs={"type": "information"}), post2)
        data = response.content.decode("utf-8")
        self.assertTrue("Change success" in data)
        self.assertTrue("changefirst" in data)
        self.assertTrue("changesecond" in data)
        self.assertTrue("changeemail" in data)

        response = self.client.post(reverse("change", kwargs={"type": "password"}), post3)
        data = response.content.decode('utf-8')
        self.assertTrue("Two passwords are different!" in data)

        response = self.client.post(reverse("change", kwargs={"type": "password"}), post4)
        data = response.content.decode('utf-8')
        self.assertTrue("Password cannot be empty" in data)

        response = self.client.post(reverse("change", kwargs={"type": "information"}), post5)
        data = response.content.decode('utf-8')
        self.assertTrue("Email cannot be empty" in data)

        response = self.client.get(reverse("logout"))
        data = response.content.decode('utf-8')
        self.assertTrue("logged out" in data)
        login = self.client.login(username="User1", password="change")
        self.assertEqual(login, True)

class GroupAndMeetingTest(TestCase):

    def convert(self, ddatetime):
        if ddatetime:
            ddatetime = ddatetime.split(' ')[0]
            # print(ddatetime)\
            ddatetime = ddatetime.split('+')[0]
            return datetime.datetime.strptime(ddatetime, '%Y-%m-%dT%H:%M:%S')
        return


    def setUp(self):
        self.client = Client()

        # User1: Not in any group or meeting
        self.User1 = User.objects.create_user(username="User1", first_name="first1",
                                              last_name="last1", email="useremail1@server.com",
                                              password="password1")
        calendar1 = Calendar(name="User1"+"_cal", slug="User1")
        calendar1.save()
        calendar1.create_relation(self.User1)

        # User2: admin of Group1, Meeting1
        self.User2 = User.objects.create_user(username="User2", first_name="first2",
                                              last_name="last2", email="useremail2@server.com",
                                              password="password2")
        calendar2 = Calendar(name="User2"+"_cal", slug="User2")
        calendar2.save()
        calendar2.create_relation(self.User2)

        # User3, Not in any group or meeting
        self.User3 = User.objects.create_user(username="User3", first_name="first3",
                                              last_name="last3", email="useremail3@server.com",
                                              password="password3")
        calendar3 = Calendar(name="User3"+"_cal", slug="User3")
        calendar3.save()
        calendar3.create_relation(self.User3)

        # User4, In Group1, Meeting1
        self.User4 = User.objects.create_user(username="User4", first_name="first4",
                                              last_name="last3", email="useremail3@server.com",
                                              password="password3")
        calendar4 = Calendar(name="User4"+"_cal", slug="User4")
        calendar4.save()
        calendar4.create_relation(self.User4)

        self.Group1 = Group.objects.create(name="Group1", admin=self.User2)
        self.Membership12 = Membership.objects.create(group=self.Group1, member=self.User2)
        self.Membership14 = Membership.objects.create(group=self.Group1, member=self.User4)
        self.Meeting1 = Meeting.objects.create(group=self.Group1, title="testtitle",
                                               description="testdescription",
                                               start_time=self.convert('2017-12-04T00:00:00'),
                                               end_time=self.convert('2017-12-05T00:00:00'))
        self.Event2 = Event.objects.create(start=self.convert('2017-12-04T00:00:00'),
                                           end=self.convert('2017-12-05T00:00:00'),
                                           title=self.Meeting1.title,
                                           description=self.Meeting1.description,
                                           creator=self.User2, calendar_id=calendar2.id)

        self.Event4 = Event.objects.create(start=self.convert('2017-12-04T00:00:00'),
                                           end=self.convert('2017-12-05T00:00:00'),
                                           title=self.Meeting1.title,
                                           description=self.Meeting1.description,
                                           creator=self.User4, calendar_id=calendar4.id)

        self.MeetingEventRelationship12 = MeetingEventRelationship.objects.create    \
                                          (meeting=self.Meeting1, event=self.Event2)
        self.MeetingEventRelationship14 = MeetingEventRelationship.objects.create    \
                                          (meeting=self.Meeting1, event=self.Event4)

    def test_send_message(self):
        login = self.client.login(username="User2", password="password2")
        message = "test send message\n"
        post1 = {"username": self.User4.username}
        status = messageHandler.send_message(self.User2, self.User4, message)
        response = self.client.post(reverse("view_notification"), post1)
        data = response.content.decode('utf-8')
        self.assertTrue("test send message" in data)

    def test_create_and_view_a_group(self):
        login = self.client.login(username="User1", password="password1")
        post1 = {"name": "newgroup"}
        post2 = {"username": "User1"}
        post3 = {"name": "Group1"}
        response = self.client.post(reverse("creategroup"), post3)
        group = Group.objects.filter(name="Group1")
        self.assertEqual(len(group), 1)
        response = self.client.post(reverse("creategroup"), post1)
        group = Group.objects.filter(name="newgroup")
        self.assertEqual(len(group), 1)

        #test redirect to home
        data = response.content.decode("utf-8")
        self.assertRedirects(response, reverse('home'))
        response = self.client.get(reverse("viewallgroups"))
        data = response.content.decode('utf-8')
        self.assertTrue("My Group" in data)
        response = self.client.post(reverse("viewadmingroups"), post2)
        data = json.loads(response.content.decode('utf-8'))

        #test newly created group is shown
        self.assertEqual(data["admin"], ["newgroup"])
        self.assertEqual(data["member"], ["newgroup"])
        # notice! Haven't tested the meeting shown

    def test_delete_group(self):
        login = self.client.login(username="User2", password="password2")
        post1 = {"groupid": "Group1", "operationuser": "User1"} # User1 doesn't have authorization
        post2 = {"groupid": "Group1", "operationuser": "User2"} # User2 has authorization
        post3 = {"username": "User4"}
        response = self.client.post(reverse("deletegroup"), post1)
        groups = Group.objects.filter(name="Group1")
        membership = Membership.objects.filter(group="Group1")
        meetingMembership = MeetingEventRelationship.objects.filter(meeting=self.Meeting1)
        self.assertEqual(len(groups), 1)
        self.assertEqual(len(membership), 2)
        self.assertEqual(len(meetingMembership), 2)
        response = self.client.post(reverse("deletegroup"), post2)
        groups = Group.objects.filter(name="Group1")
        membership = Membership.objects.filter(group=self.Group1)
        meeting = Meeting.objects.filter(group=self.Group1)
        meetingMembership = MeetingEventRelationship.objects.filter(meeting=self.Meeting1)
        self.assertEqual(len(groups), 0)
        self.assertEqual(len(membership), 0)
        self.assertEqual(len(meeting), 0)
        self.assertEqual(len(meetingMembership), 0)

        # user4 could view the notification of group delete
        response = self.client.post(reverse("view_notification"), post3)
        data = response.content.decode('utf-8')
        self.assertTrue("Group1 is removed" in data)
        self.assertTrue("You are removed from group Group1" in data)
        self.assertTrue("You are removed from meeting testtitle" in data)

    def test_add_member_and_accept_or_reject_group_invitation(self):
        login = self.client.login(username="User2", password="password2")
        post1 = {"group_name": "Group1", "memberid": "User1",
                 "group_admin": "User2", "messages": "hello"}
        post2 = {"group_name": "Group1", "memberid": "User10",
                 "group_admin": "User2", "messages": "hello"}
        post3 = {"group_name": "Group1", "memberid": "User3",
                 "group_admin": "User1", "messages": "hello"}
        post4 = {"group_name": "Group1", "username": "User1"}
        response = self.client.post(reverse("addnewmember"), post1)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data["valid"], "true")
        response = self.client.post(reverse("addnewmember"), post2)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data["valid"], "false-nomember")
        response = self.client.post(reverse("addnewmember"), post3)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data["valid"], "false-noright")

        # the invitation of User1 exists
        invitation = GroupInvitation.objects.filter(recipient=self.User1)
        self.assertEqual(len(invitation), 1)
        self.assertEqual(invitation[0].status, 'NO')

        # reject the group invitation
        response = self.client.post(reverse("reject_group"), post4)
        membership = Membership.objects.filter(group="Group1", member=self.User1)
        invitation = GroupInvitation.objects.filter(recipient=self.User1)
        self.assertEqual(len(membership), 0)
        self.assertEqual(invitation[0].status, 'RJ')

        # accept the group invitation
        response = self.client.post(reverse("accept"), post4)
        membership = Membership.objects.filter(group="Group1", member=self.User1)
        self.assertEqual(len(membership), 1) #accept invitation from group for the first time
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data["valid"], "true")
        self.assertEqual(invitation[0].status, 'AC')

        response = self.client.post(reverse("accept"), post4)
        membership = Membership.objects.filter(group="Group1", member=self.User1)
        self.assertEqual(len(membership), 1) #accept invitation from group for the second time
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data["valid"], "false")



    def test_view_one_group(self):
        login = self.client.login(username="User2", password="password2")
        Membership.objects.create(group=self.Group1, member=self.User1)
        post1 = {"group_name": "Group1"}
        response = self.client.post(reverse("showgroup"), post1)
        data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(data["admin"], "User2")
        self.assertTrue("User1" in data["member"])
        self.assertTrue("User2" in data["member"])


    def test_delete_member_from_group(self):
        login = self.client.login(username="User2", password="password2")
        Membership.objects.create(group=self.Group1, member=self.User1)
        # delete member in the group(attend a meeting)
        post1 = {"group_name": "Group1", "memberid": "User4", "operationuser": "User2"}
        # admin should not be able to delete himself/herself
        post2 = {"group_name": "Group1", "memberid": "User2", "operationuser": "User2"}
        post3 = {"group_name": "Group1", "memberid": "User3", "operationuser": "User1"}
        post4 = {"username": "User4"}
        response = self.client.post(reverse("deletemember"), post1)
        data = json.loads(response.content.decode("utf-8"))
        membership = Membership.objects.filter(member=self.User4)
        meetingmembership = MeetingEventRelationship.objects.filter(meeting=self.Meeting1)
        self.assertEqual(len(meetingmembership), 1)
        self.assertEqual(len(membership), 0)
        self.assertEqual(data["valid"], "true")
        response = self.client.post(reverse("view_notification"), post4)
        data = response.content.decode("utf-8")
        self.assertTrue("You are removed from group Group1" in data)
        self.assertTrue("You are removed from meeting testtitle" in data)
        response = self.client.post(reverse("deletemember"), post2)
        data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(data["valid"], "false-self")
        response = self.client.post(reverse("deletemember"), post3)
        data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(data["valid"], "false-noright")

    def test_create_and_view_meeting_and_invitation(self):
        login = self.client.login(username="User2", password="password2")
        post1 = {"group_name": "Group1", "title": "title2", "description": "description2",
                 "start_time": "2017-08-15", "end_time": "2017-08-16"}
        post2 = {"group_name": "Group1", "title": "title2", "description": "description2",
                 "end_time": "2017-08-16"}
        post3 = {"group_name": "Group1"}
        post4 = {"username": "User4"}
        # notice! haven't tested time empty
        response = self.client.post(reverse("add_meeting"), post1)
        meeting = Meeting.objects.filter(group='Group1')
        mer = MeetingEventRelationship.objects.filter(meeting=meeting[1])
        self.assertEqual(len(meeting), 2)
        self.assertEqual(len(mer), 1)
        data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(data["valid"], "true")
        # test view meetings
        response = self.client.post(reverse("show_meetings"), post3)
        data = response.content.decode("utf-8")
        self.assertTrue("title2" in data)
        self.assertTrue("description2" in data)
        self.assertTrue("User2" in data)
        # test view invitation
        response = self.client.post(reverse("view_meetinginvitation"), post4)
        data = response.content.decode("utf-8")
        self.assertTrue("title2" in data)
        self.assertTrue("description2" in data)


    def test_handle_meeting_invitation(self):
        login = self.client.login(username="User2", password="password2")
        post1 = {"group_name": "Group1", "title": "title2", "description": "description2",
                 "start_time": "2017-08-15T00:00:00", "end_time": "2017-08-16T00:00:00"}
        post2 = {"username": "User4"}
        meeting_info = []
        meeting_info.append("title2")
        meeting_info.append("description2")
        meeting_info.append("Group1")
        meeting_info.append("2017-08-15T00:00:00")
        meeting_info.append("2017-08-16T00:00:00")

        meeting_info_rej = []
        meeting_info_rej.append("title2")
        meeting_info_rej.append("Group1")

        #first add a meeting to send invitation
        response = self.client.post(reverse("add_meeting"), post1)
        response = self.client.post(reverse("view_meetinginvitation"), post2)
        data = response.content.decode("utf-8")
        data = json.loads(data)
        # get the meeting id
        meetingid = data[0]['meeting']['id']
        meeting_info.append(meetingid)
        meeting_info_rej.append(meetingid)
        post3 = {"meeting_info[]": meeting_info, "username": "User4"}
        post4 = {"meeting_info[]": meeting_info_rej, "username":"User4"}
        # reject the meeting
        response = self.client.post(reverse("reject_meeting"), post4)
        meeting = Meeting.objects.filter(id=meetingid)
        self.assertEqual(len(meeting), 1)
        mer = MeetingEventRelationship.objects.filter(meeting=meeting)
        self.assertEqual(len(mer), 1)
        # accept the meeting
        response = self.client.post(reverse("accept_meeting"), post3)
        meeting = Meeting.objects.filter(id=meetingid)
        self.assertEqual(len(meeting), 1)
        mer = MeetingEventRelationship.objects.filter(meeting=meeting[0])
        self.assertEqual(len(mer), 2)
        data = response.content.decode("utf-8")
        data = json.loads(data)
        self.assertEqual(data['valid'], 'true')

        # accept the meeting twice
        response = self.client.post(reverse("accept_meeting"), post3)
        meeting = Meeting.objects.filter(id=meetingid)
        mer = MeetingEventRelationship.objects.filter(meeting=meeting[0])
        self.assertEqual(len(mer), 2)
        data = response.content.decode("utf-8")
        data = json.loads(data)
        self.assertEqual(data['valid'], 'true')

    def test_change_meeting(self):
        login = self.client.login(username="User2", password="password2")
        meetingid = self.Meeting1.id
        post1 = {"id": meetingid, "group_name": "Group1", 'changed_title': "changed_t",
                 "changed_description": "changed_d",
                 "changed_start_time": "2017-08-21T00:00:00", "changed_end_time":
                 "2017-08-21T01:00:00"}
        post2 = {"username": "User4"}
        response = self.client.post(reverse("change_meeting"), post1)
        meetings = Meeting.objects.all()
        self.assertEqual(len(meetings), 1)
        meeting = Meeting.objects.filter(id=self.Meeting1.id)
        mer = MeetingEventRelationship.objects.filter(meeting=self.Meeting1)
        self.assertEqual(len(mer), 0)
        self.assertEqual(len(meeting), 0)

        # old meeting is deleted
        response = self.client.post(reverse("view_notification"), post2)
        data = response.content.decode("utf-8")
        self.assertTrue("Meeting testtitle is deleted" in data)
        # new meeting sends invitation to the member
        response = self.client.post(reverse("view_meetinginvitation"), post2)
        data = response.content.decode("utf-8")
        self.assertTrue("changed_t" in data)

    def test_delete_meeting(self):
        login = self.client.login(username="User2", password="password2")
        meetingid = self.Meeting1.id
        post1 = {"id": meetingid}
        response = self.client.post(reverse("delete_meeting"), post1)
        meeting = Meeting.objects.filter(id=self.Meeting1.id)
        self.assertEqual(len(meeting), 0)
        mer = MeetingEventRelationship.objects.filter(meeting=self.Meeting1)
        self.assertEqual(len(mer), 0)
