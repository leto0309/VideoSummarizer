import unittest
import os
import threading
from unittest.mock import Mock, patch

import bookmark_launcher as link


class BookmarkTests(unittest.TestCase):
    def test_only_fixed_uri_accepted(self):
        for value in (link.URI, link.URI + '/'):
            link.validate_uri(value)
        for value in ('https://example.com', 'videosummarizer://open?cmd=calc',
                      'videosummarizer://open/anything', 'videosummarizer://other',
                      'videosummarizer://open#data', 'videosummarizer://open " & calc'):
            with self.assertRaises(ValueError):
                link.validate_uri(value)

    @patch.object(link, 'log')
    @patch.object(link, 'services_ready', return_value=True)
    def test_existing_services_are_reused(self, ready, log):
        launch, browser = Mock(), Mock()
        link.open_on_demand(Mock(), launch, browser)
        launch.assert_not_called()
        browser.assert_called_once_with(link.WEB_URL)

    @patch.object(link, 'log')
    @patch.object(link, 'time')
    @patch.object(link, 'project_process', return_value=False)
    @patch.object(link, 'services_ready', side_effect=[False, False, True])
    @patch.object(link.Path, 'write_text')
    def test_missing_services_start_once_and_wait_for_readiness(self, write, ready, owned, clock, log):
        clock.monotonic.return_value = 0
        process = Mock(pid=123)
        process.poll.return_value = None
        launch, browser = Mock(return_value=process), Mock()
        link.open_on_demand(Mock(), launch, browser)
        launch.assert_called_once()
        browser.assert_called_once_with(link.WEB_URL)
        self.assertEqual(ready.call_count, 3)

    @patch.object(link, 'log')
    @patch.object(link, 'time')
    @patch.object(link, 'project_process', return_value=False)
    @patch.object(link, 'services_ready', return_value=False)
    @patch.object(link.Path, 'write_text')
    def test_failed_start_does_not_open_browser(self, write, ready, owned, clock, log):
        clock.monotonic.return_value = 0
        process = Mock(pid=123)
        process.poll.return_value = 1
        browser = Mock()
        with self.assertRaisesRegex(RuntimeError, '啟動器已退出'):
            link.open_on_demand(Mock(), Mock(return_value=process), browser)
        browser.assert_not_called()

    @patch.object(link, 'project_process', return_value=False)
    @patch.object(link, 'healthy', side_effect=[True, True])
    def test_unknown_port_owner_is_rejected(self, health, owned):
        with self.assertRaisesRegex(RuntimeError, '8501'):
            link.services_ready(Mock())

    @unittest.skipUnless(os.name == 'nt', 'Windows mutex')
    def test_concurrent_clicks_wait_for_startup_mutex(self):
        started, entered = threading.Event(), threading.Event()
        errors = []
        def second_click():
            try:
                started.set()
                with link.StartupMutex():
                    entered.set()
            except Exception as exc:
                errors.append(exc)
        with link.StartupMutex():
            worker = threading.Thread(target=second_click, daemon=True)
            worker.start()
            self.assertTrue(started.wait(2))
            self.assertFalse(entered.wait(.1))
        worker.join(3)
        self.assertFalse(worker.is_alive())
        self.assertFalse(errors)
        self.assertTrue(entered.is_set())


if __name__ == '__main__':
    unittest.main()
