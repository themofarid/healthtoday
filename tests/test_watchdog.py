import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from tools.offers import Offer
from tools.watchdog import ERROR_PHRASES, check_link, http_fetch, run_watchdog


def offer(**kw):
    base = dict(slug="a", name="A", network="digistore24", link="https://www.digistore24.com/redir/1/2/k",
                link_mode="hoplink", tags=[], status="live", strikes=0)
    base.update(kw)
    return Offer(**base)


def ok_fetch(url):
    return 200, "https://vendor.example/sales", "Welcome. Buy now."


def fail_fetch(url):
    return 404, "https://vendor.example/missing", "Not here"


def boom_fetch(url):
    raise OSError("timed out")


class CheckLinkTests(unittest.TestCase):
    def test_ok_when_redirects_to_vendor(self):
        r = check_link(offer(), ok_fetch)
        self.assertTrue(r.ok)
        self.assertEqual(r.final_url, "https://vendor.example/sales")

    def test_not_ok_when_final_host_equals_link_host(self):
        same = lambda url: (200, "https://www.digistore24.com/error", "hi")
        self.assertFalse(check_link(offer(), same).ok)

    def test_direct_tracking_may_stay_on_same_host(self):
        o = offer(link="https://vendor.example/landing", link_mode="direct_tracking")
        same = lambda url: (200, "https://vendor.example/landing", "Welcome")
        self.assertTrue(check_link(o, same).ok)

    def test_not_ok_on_404(self):
        r = check_link(offer(), fail_fetch)
        self.assertFalse(r.ok)
        self.assertIn("404", r.reason)

    def test_not_ok_on_error_phrase_any_case(self):
        phrase = ERROR_PHRASES[0].upper()
        f = lambda url: (200, "https://vendor.example/x", f"Sorry: {phrase} here")
        self.assertFalse(check_link(offer(), f).ok)

    def test_fetch_exception_counts_as_failure(self):
        r = check_link(offer(), boom_fetch)
        self.assertFalse(r.ok)
        self.assertEqual(r.reason, "unreachable")

    def test_same_rules_for_both_networks(self):
        cb = offer(network="clickbank", link="https://aff.vendor.hop.clickbank.net")
        self.assertTrue(check_link(cb, ok_fetch).ok)
        self.assertFalse(check_link(cb, fail_fetch).ok)


class RunWatchdogTests(unittest.TestCase):
    def test_single_failure_adds_strike_not_dead(self):
        (o,), newly = run_watchdog([offer()], boom_fetch)
        self.assertEqual((o.strikes, o.status), (1, "live"))
        self.assertEqual(newly, [])

    def test_second_consecutive_failure_marks_dead(self):
        (o,), newly = run_watchdog([offer(strikes=1)], fail_fetch)
        self.assertEqual((o.strikes, o.status), (2, "dead"))
        self.assertEqual([n.slug for n in newly], ["a"])

    def test_already_dead_offer_is_not_reported_again(self):
        (o,), newly = run_watchdog([offer(strikes=2, status="dead")], fail_fetch)
        self.assertEqual(o.status, "dead")
        self.assertEqual(newly, [])

    def test_success_resets_strikes(self):
        (o,), _ = run_watchdog([offer(strikes=1)], ok_fetch)
        self.assertEqual((o.strikes, o.status), (0, "live"))

    def test_dead_offer_revives_when_ok(self):
        (o,), newly = run_watchdog([offer(strikes=2, status="dead")], ok_fetch)
        self.assertEqual((o.strikes, o.status), (0, "live"))
        self.assertEqual(newly, [])

    def test_paused_offers_are_skipped(self):
        calls = []
        def spy(url):
            calls.append(url)
            return ok_fetch(url)
        paused = offer(status="paused", strikes=1)
        (o,), _ = run_watchdog([paused], spy)
        self.assertEqual(o, paused)
        self.assertEqual(calls, [])


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/redir":
            self.send_response(302)
            self.send_header("Location", "/vendor")
            self.end_headers()
        elif self.path == "/vendor":
            body = b"Vendor sales page"
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.send_header("Content-Length", "0")
            self.end_headers()

    def log_message(self, *args):
        pass


class HttpFetchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), _Handler)
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_http_fetch_follows_redirect_and_returns_final_url(self):
        status, final, body = http_fetch(self.base + "/redir")
        self.assertEqual((status, final), (200, self.base + "/vendor"))
        self.assertIn("Vendor sales page", body)

    def test_http_fetch_returns_status_for_404(self):
        status, _, _ = http_fetch(self.base + "/nope")
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
