import unittest
from schedule.views.CreateEventView import form_valid

class TestCreateEvent(unittest.TestCase):

    form = 
    def test_form_valid(self, form):
        test = CreateEventView



    def test_split(self):
        s = 'hello world'
        self.assertEqual(s.split(), ['hello', 'world'])
        # check that s.split fails when the separator is not a string
        with self.assertRaises(TypeError):
            s.split(2)

if __name__ == '__main__':
    unittest.main()