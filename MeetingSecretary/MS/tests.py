import json
import codecs
from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from MS.models import Group, Membership
from MS import views
from MS.forms import SignUpForm, CreatePartialGroupForm
from django.core.urlresolvers import reverse

# Create your tests here.
class PersonalProfileTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.User1 = User.objects.create_user(username="User1", first_name="first1", last_name="last1", email="useremail1@server.com", password="password1")
        self.User2 = User.objects.create_user(username="User2", first_name="first2", last_name="last2", email="useremail2@server.com", password="password2")

    def test_signup(self):
        post1 = {"username": "TestUser1", "first_name": "FN1", "last_name": "LN1", "email": "email1@server.com", "password1": "passwordtest", "password2": "passwordtest"}
        # two passwords are different
        post2 = {"username": "TestUser2", "first_name": "FN2", "last_name": "LN2", "email": "email2@server.com", "password1": "passwordtest", "password2": "passwordtest2"}
        response = self.client.post(reverse("signup"), post1)
        self.assertEqual(response.status_code, 302)
        response = self.client.post(reverse("signup"), post2)
        self.assertEqual(response.status_code, 200)
        Testuser1 = User.objects.get(username="TestUser1")
        Testuser2 = User.objects.filter(username="TestUser2")
        self.assertEqual(Testuser1.first_name, "FN1")
        self.assertEqual(Testuser1.email, "email1@server.com")
        # Test password hash
        self.assertNotEqual(Testuser1.password, "passwordtest")
        self.assertEqual(len(Testuser2), 0)

    def test_login(self):
        login = self.client.login(username="User1", password="password1")
        self.assertEqual(login, True)

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
        # one password is empty
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

class GroupTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.User1 = User.objects.create_user(username="User1", first_name="first1", last_name="last1", email="useremail1@server.com", password="password1")
        self.User2 = User.objects.create_user(username="User2", first_name="first2", last_name="last2", email="useremail2@server.com", password="password2")
        self.User3 = User.objects.create_user(username="User3", first_name="first3", last_name="last3", email="useremail3@server.com", password="password3")
        self.Group1 = Group.objects.create(name="Group1", admin=self.User2)
        self.Membership = Membership.objects.create(group=self.Group1, member=self.User2)

    def test_create_and_view(self):
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
        # If there are groups with same name?

    def test_delete_group(self):
        login = self.client.login(username="User2", password="password2")
        post1 = {"groupid": "Group1", "operationuser": "User1"} # User1 doesn't have authorization
        post2 = {"groupid": "Group1", "operationuser": "User2"} # User2 has authorization
        response = self.client.post(reverse("deletegroup"), post1)
        groups = Group.objects.filter(name="Group1")
        membership = Membership.objects.filter(group="Group1")
        self.assertEqual(len(groups), 1)
        self.assertEqual(len(membership), 1)
        response = self.client.post(reverse("deletegroup"), post2)
        groups = Group.objects.filter(name="Group1")
        membership = Membership.objects.filter(group="Group1")
        self.assertEqual(len(groups), 0)
        self.assertEqual(len(membership), 0)

    def test_add_member_and_accept(self):
        login = self.client.login(username="User2", password="password2")
        post1 = {"group_name": "Group1", "memberid": "User1", "operationuser": "User2", "messages": "hello"}
        post2 = {"group_name": "Group1", "memberid": "User4", "operationuser": "User2", "messages": "hello"}
        post3 = {"group_name": "Group1", "memberid": "User3", "operationuser": "User1", "messages": "hello"}
        post4 = {"groupname": "Group1", "username": "User1"}
        response = self.client.post(reverse("addnewmember"), post1)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data["valid"], "true")
        response = self.client.post(reverse("addnewmember"), post2)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data["valid"], "false")
        response = self.client.post(reverse("addnewmember"), post3)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data["valid"], "false")
        response = self.client.post(reverse("accept"), post4)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data["valid"], "true")


    def test_view_one_group(self):
        login = self.client.login(username="User2", password="password2")
        Membership.objects.create(group=self.Group1, member=self.User1)
        post1 = {"group_name": "Group1"}
        response = self.client.post(reverse("showgroup"), post1)
        data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(data["admin"], "User2")
        self.assertTrue("User1" in data["member"])
        self.assertTrue("User2" in data["member"])


    def test_delete_member(self):
        login = self.client.login(username="User2", password="password2")
        Membership.objects.create(group=self.Group1, member=self.User1)
        post1 = {"group_name": "Group1", "memberid": "User1", "operationuser": "User2"}
        post2 = {"group_name": "Group1", "memberid": "User2", "operationuser": "User2"} # admin should not be able to delete himself/herself
        post3 = {"group_name": "Group1", "memberid": "User3", "operationuser": "User1"}
        response = self.client.post(reverse("deletemember"), post1)
        data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(data["valid"], "true")
        response = self.client.post(reverse("deletemember"), post2)
        data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(data["valid"], "false")
        response = self.client.post(reverse("deletemember"), post3)
        data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(data["valid"], "false")
