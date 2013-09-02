import unittest

from mock import Mock
from mock import patch


class TestAggregateTrends(unittest.TestCase):

    @patch('ripl.core.decorators.users')
    @patch('ripl.core.api.controller.aggregate')
    def test_aggregate(self, mock_aggregate, mock_users):
        """Ensure aggregate_trends works correctly when the current user is an
        admin.
        """
        from ripl.core.api.controller import aggregate_trends

        mock_users.get_current_user.return_value = Mock()
        mock_users.is_current_user_admin.return_value = True

        _, status = aggregate_trends()

        mock_aggregate.assert_called_once_with()
        self.assertEqual(200, status)

