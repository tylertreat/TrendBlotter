import unittest

from mock import patch

from blotter.core.aggregation.client.gplus import get_worldwide_trends


@patch('blotter.core.aggregation.client.gplus.urllib2.urlopen')
class TestGetWorldwideTrends(unittest.TestCase):

    def test_happy_path(self, mock_urlopen):
        """Verify get_worldwide_trends retrieves the top 10 trends from
        Google+.
        """

        mock_urlopen.return_value.read.return_value = \
            """<span class="Jo"><a href="s/%23HappyBirthdayViru/posts"
        target="_top" class="d-s ob FSc"
        tabindex="0">#HappyBirthdayViru</a></span></div><div
        class="Xp"></div></li><li class="Zz fj A2" rowindex="1"><div class="N5
        Mq"><div class="VZb qVd"></div><span class="Jo"><a
        href="s/Red%20Sox/posts" target="_top" class="d-s ob FSc"
        tabindex="0">Red Sox</a></span></div><div class="Xp"></div></li><li
        class="Zz fj A2" rowindex="2"><div class="N5 Mq"><div class="VZb
        qVd"></div><span class="Jo"><a href="s/Facebook/posts" target="_top"
        class="d-s ob FSc" tabindex="0">Facebook</a></span></div><div
        class="Xp"></div></li><li class="Zz fj A2" rowindex="3"><div class="N5
        Mq"><div class="VZb tVd"></div><span class="Jo"><a
        href="s/%23Epic/posts" target="_top" class="d-s ob FSc"
        tabindex="0">#Epic</a></span></div><div class="Xp"></div></li><li
        class="Zz fj A2" rowindex="4"><div class="N5 Mq"><div class="VZb
        qVd"></div><span class="Jo"><a href="s/%23Halloween2013/posts"
        target="_top" class="d-s ob FSc"
        tabindex="0">#Halloween2013</a></span></div><div
        class="Xp"></div></li></ul></div></div><div class="xj"><div
        class="q3"><ul class="Bx wg"><li class="Zz fj A2" rowindex="5"><div
        class="N5 Mq"><div class="VZb tVd"></div><span class="Jo"><a
        href="s/New%20Delhi/posts" target="_top" class="d-s ob FSc"
        tabindex="0">New Delhi</a></span></div><div class="Xp"></div></li><li
        class="Zz fj A2" rowindex="6"><div class="N5 Mq"><div class="VZb
        rVd"></div><span class="Jo"><a
        href="s/Drone%20attacks%20in%20Pakistan/posts" target="_top" class="d-s
        ob FSc" tabindex="0">Drone attacks in Pakistan</a></span></div><div
        class="Xp"></div></li><li class="Zz fj A2" rowindex="7"><div class="N5
        Mq"><div class="VZb qVd"></div><span class="Jo"><a
        href="s/%23FallColors/posts" target="_top" class="d-s ob FSc"
        tabindex="0">#FallColors</a></span></div><div class="Xp"></div></li><li
        class="Zz fj A2" rowindex="8"><div class="N5 Mq"><div class="VZb
        qVd"></div><span class="Jo"><a href="s/Taylor%20Swift/posts"
        target="_top" class="d-s ob FSc" tabindex="0">Taylor
        Swift</a></span></div><div class="Xp"></div></li><li class="Zz fj A2"
        rowindex="9"><div class="N5 Mq"><div class="VZb qVd"></div><span
        class="Jo"><a href="s/%23Moon/posts" target="_top" class="d-s ob FSc"
        tabindex="0">#Moon</a></span>"""

        actual = get_worldwide_trends()

        self.assertEqual([('#Moon', 1), ('Taylor Swift', 2),
                          ('#FallColors', 3), ('Drone attacks in Pakistan', 4),
                          ('New Delhi', 5), ('#Halloween2013', 6),
                          ('#Epic', 7), ('Facebook', 8), ('Red Sox', 9),
                          ('#HappyBirthdayViru', 10)], actual)

        mock_urlopen.assert_called_once_with('https://plus.google.com/s/a')

    def test_sad_path(self, mock_urlopen):
        """Verify get_worldwide_trends returns an empty list when the HTTP
        request fails.
        """

        def side_effect(url):
            import urllib2
            raise urllib2.URLError('Oh snap')

        mock_urlopen.side_effect = side_effect

        actual = get_worldwide_trends()

        self.assertEqual([], actual)
        mock_urlopen.assert_called_once_with('https://plus.google.com/s/a')

