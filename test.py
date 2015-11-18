import unittest
import threading
import BaseHTTPServer

from urlz import request, UnexpectedResponse


class ClientTests(unittest.TestCase):
    client = request.from_url('http://127.0.0.1:19009/')

    def test_from_url(self):
        """ Test that Request can be constructed from URL """
        req = request.from_url('http://|"\'@%s:s@a.b.c.com:90/abc?yes=1#boo',
                               body='a')
        self.assertEqual(req, ('GET', 'a.b.c.com', '/abc', {'yes': '1'}, {},
                               'a', '|"\'@%s', 's', 90, 'http'))

    def test_path_indexing(self):
        """ Test that path can be manipulated by accessing a path """
        req = request.from_url('a')['b']
        self.assertEqual('a/b', req.path)

    def test_replace(self):
        """ Test getting new instance via path replace() """
        r1 = request.from_url('a')
        r2 = r1.replace(path='b')
        self.assertNotEqual(r1, r2)
        self.assertEqual(r2.path, 'b')

    def test_immutable(self):
        """ Test that property is immutable """
        req = request.from_url('a')
        with self.assertRaises(AttributeError):
            req.path = 'b'

    def test_200(self):
        res = self.client.response
        self.assertEqual((200, 'ok'), (res.status, res.data))

    def test_300(self):
        redir = self.client['redirect']
        self.assertEqual(301, redir.execute(redirect=False).status)
        self.assertEqual(200, redir.response.status)

    def test_not_200(self):
        with self.assertRaises(UnexpectedResponse):
            self.client['fail'].response

    def test_not_json(self):
        with self.assertRaises(UnexpectedResponse):
            self.client['notjson'].json

    class TestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
        def do_GET(self, *args):
            if self.path == '/fail':
                self.send_error(400)
            elif self.path == '/redirect':
                self.send_response(301)
                self.send_header('Location', '/')
            else:
                self.wfile.write('ok')

    @classmethod
    def setUpClass(cls):
        server = BaseHTTPServer.HTTPServer(('127.0.0.1', 19009),
                                           cls.TestHandler)
        cls.http_stop = False
        def run():
            while not cls.http_stop:
                server.handle_request()
        threading.Thread(target=run).start()

    @classmethod
    def tearDownClass(cls):
        cls.http_stop = True
        cls.client['quit'].execute()


if __name__ == '__main__':
    unittest.main()
