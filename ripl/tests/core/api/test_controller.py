import unittest

from mock import Mock
from mock import patch


class TestAggregateTrends(unittest.TestCase):

    @patch('ripl.core.decorators.users')
    @patch('ripl.core.api.controller.aggregate')
    def test_works_as_admin(self, mock_aggregate, mock_users):
        """Ensure aggregate_trends works correctly when the current user is an
        admin.
        """
        from ripl.core.api.controller import aggregate_trends

        mock_users.get_current_user.return_value = Mock()
        mock_users.is_current_user_admin.return_value = True

        aggregate_trends()

        mock_aggregate.assert_called_once_with()

    @patch('ripl.core.decorators.users')
    @patch('ripl.core.api.controller.aggregate')
    def test_does_not_work_as_user(self, mock_aggregate, mock_users):
        """Ensure aggregate_trends raises a 401 code when invoked by a user
        that is not an admin.
        """
        from werkzeug.exceptions import Unauthorized
        from ripl.core.api.controller import aggregate_trends

        mock_users.get_current_user.return_value = Mock()
        mock_users.is_current_user_admin.return_value = False

        with self.assertRaises(Unauthorized) as cm:
            aggregate_trends()

        self.assertIsInstance(cm.exception, Unauthorized)
        self.assertFalse(mock_aggregate.called)

    @patch('ripl.core.decorators.request')
    @patch('ripl.core.decorators.redirect')
    @patch('ripl.core.decorators.users')
    @patch('ripl.core.api.controller.aggregate')
    def test_redirects(self, mock_aggregate, mock_users, mock_redirect,
                       mock_request):
        """Ensure aggregate_trends issues a redirect when there is no user."""
        from ripl.core.api.controller import aggregate_trends

        mock_users.get_current_user.return_value = None
        expected = 'foo'
        mock_request.url = 'url'
        mock_users.create_login_url.return_value = expected

        aggregate_trends()

        mock_redirect.assert_called_once_with(expected)
        self.assertFalse(mock_aggregate.called)

