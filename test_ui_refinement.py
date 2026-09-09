"""Assignment edits retain the keys consumed by condition persistence."""
import unittest

from streamlit.testing.v1 import AppTest


class PartyPickerTests(unittest.TestCase):
    def test_assignment_changes_and_clear_survive_reruns(self):
        app = AppTest.from_string('''
import streamlit as st
from ui_refinement import party_picker
party_picker('Responsible parties', ['Borrower', 'Co-Borrower', 'Title'],
             default=['Borrower'], key='scan_example_party')
st.write(st.session_state['scan_example_party'])
''', default_timeout=30).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.get('popover')[0].proto.popover.label, 'Borrower')
        app.multiselect[0].select('Co-Borrower').run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state['scan_example_party'], ['Borrower', 'Co-Borrower'])
        self.assertEqual(app.get('popover')[0].proto.popover.label, 'Borrower +1')
        app.multiselect[0].select('Title').run()
        self.assertEqual(app.get('popover')[0].proto.popover.label, 'Borrower +2')
        app.multiselect[0].set_value([]).run()
        app.run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state['scan_example_party'], [])
        self.assertEqual(app.get('popover')[0].proto.popover.label, 'Assign party')


if __name__ == '__main__':
    unittest.main()
