import unittest

from mock import patch


class TestAggregateTrends(unittest.TestCase):

    @patch('blotter.core.api.controller.Async')
    def test_aggregate(self, mock_async):
        """Ensure aggregate_trends inserts an aggregate task."""
        from blotter.core.aggregation import AGGREGATION_QUEUE
        from blotter.core.aggregation.trends import aggregate
        from blotter.core.api.controller import aggregate_trends

        mock_async.return_value = mock_async

        _, status = aggregate_trends()

        self.assertEqual(200, status)
        mock_async.assert_called_once_with(target=aggregate,
                                           queue=AGGREGATION_QUEUE)
        mock_async.start.assert_called_once_with()

