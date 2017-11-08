from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from MS import views
from django.core.urlresolvers import reverse

# Create your tests here.
class PersonalProfileTest(TestCase):

    def setup(self):
        self.client = Client()


    def test_signup(self):
        post1 = {"username": "TestUser1", "first_name": "FN1", "last_name": "LN1", "email": "email1@server.com", "password1": "passwordtest", "password2": "passwordtest"}
        post2 = {"username": "TestUser2", "first_name": "FN2", "last_name": "LN2", "email": "email2@server.com", "password1": "passwordtest", "password2": "passwordtest2"}
        response = self.client.post(reverse("signup"), post1)
        self.assertEqual(response.status_code, 302)
        response = self.client.post(reverse("signup"), post2)
        self.assertEqual(response.status_code, 200)
        user1 = User.objects.get(username="TestUser1")
        user2 = User.objects.filter(username="TestUser2")
        self.assertEqual(user1.first_name, "FN1")
        self.assertEqual(user1.email, "email1@server.com")
        self.assertNotEqual(user1.password, "passwordtest")
        self.assertEqual(len(user2), 0)

    def test_change(self):
        post1 = {"username": "TestUser1", "first_name": "FN1", "last_name": "LN1", "email": "email1@server.com", "password1": "passwordtest", "password2": "passwordtest"}
        response = self.client.post(reverse("signup"), post1)
        self.assertEqual(response.status_code, 302)
        #not finished
