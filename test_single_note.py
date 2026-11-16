import unittest
from main import classify, PRIORITY_RANK   # <-- correct constant name

class TestSingleNote(unittest.TestCase):
    def test_classify_see_now(self):
        """A note that clearly needs immediate attention should be classified as 'see_now'."""
        note = "I have severe chest pain and shortness of breath."
        result = classify(note)                 # classify() now expects only the note (wrapper in main.py handles client & prompt)
        # The function returns a dict; we check the “priority” field.
        self.assertIn("priority", result)
        self.assertEqual(result["priority"], "see_now")

if __name__ == "__main__":
    unittest.main()