from collections import namedtuple
import logging
import urllib3
import json


""" The basic immutable request properties container """
RequestTuple = namedtuple("RequestTuple",
                          "method,host,path,params,headers,body,"
                          "username,password,port,protocol")


class RequestURL(RequestTuple):
    """
    A class to represent an HTTP Request.

    Instances are immutable, that is, any change to the properties of
    the class result in a new instance.

    Example usage:

    >>> request = Request.from_url('http://graph.facebook.com/')
    >>> request
    Request(method='GET', host='graph.facebook.com', path='/', params={},
            headers={}, body=None, username=None, password=None, port=None)
    >>> request.replace(host='localhost')
    Request(method='GET', host='localhost', path='/', params={}, headers={},
            body=None, username=None, password=None, port=None)
    >>> request.with_params({'access_token': 'secret'})
    Request(method='GET', host='graph.facebook.com', path='/',
            params={'access_token': 'secret'}, headers={}, body=None,
            username=None, password=None, port=None)
    >>> request.with_params({'access_token': 'secret'}).get_url()
    'http://graph.facebook.com/?access_token=secret'
    """

    def __new__(cls, method="GET", host=None, path='/', params=None,
                headers=None, body=None, port=None, username=None,
                password=None, protocol='http'):
        return super(RequestURL, cls).__new__(
            cls, method, host, path, params or {}, headers or {},
            body, username, password, port, protocol
        )

    def with_params(self, params_dict):
        """ Update request parameters """
        new_params = self.params.copy()
        new_params.update(params_dict)
        return self._replace(params=new_params)

    def with_headers(self, headers_dict):
        """ Update headers """
        new_headers = self.headers.copy()
        new_headers.update(headers_dict)
        return self._replace(headers=new_headers)

    def __getitem__(self, item):
        """
        Append to the request path:

        >>> request.path
        '/hello/'
        >>> request['world'].path
        '/hello/world'

        This hack is to support path modification
        without breaking the tuple interface
        """
        if type(item) == int:
            return super(RequestURL, self).__getitem__(item)
        else:
            newpath = self.path.rstrip('/') + '/' + item.lstrip('/')
            return self._replace(path=newpath)

    """ Return a new instance with attribute replaced """
    replace = RequestTuple._replace

    def get_url(self):
        """ Build and return the URL of the request """
        netloc = self.host
        if self.port not in (None, 80):
            netloc += ':%s' % self.port

        params = urlencode(self.params)
        parts = (self.protocol, netloc, self.path, '', params, '')
        return urlparse.urlunparse(parts)

    @classmethod
    def from_url(cls, url, **extra_kwargs):
        """ Construct instance from URL """
        parsed = urlparse.urlparse(url)
        params = dict(urlparse.parse_qsl(parsed.query))
        kwargs = dict(
            host=parsed.hostname,
            path=parsed.path,
            params=params,
            port=parsed.port,
            username=parsed.username,
            password=parsed.password,
            protocol=parsed.scheme,
        )
        kwargs.update(extra_kwargs)
        return cls(**kwargs)


# The urlparse module is renamed to urllib.parse in Python 3.
try:
    import urllib.parse as urlparse
    from urllib.parse import urlencode
except ImportError:
    import urlparse
    from urllib import urlencode


class UnexpectedResponse(RuntimeError):
    """ Thrown when a response looks wonky """
    def __init__(self, request, response):
        self.request = request
        self.response = response
        message = "status=%s %s, data=%s" % (
            response.status,
            response.reason, response.data[:1000])
        super(UnexpectedResponse, self).__init__(message)


class cached_property(object):
    """
    Decorator that converts a method with a single self argument into a
    property cached on the instance.

    Optional ``name`` argument allows you to make cached properties of other
    methods. (e.g.  url = cached_property(get_absolute_url, name='url') )
    """
    def __init__(self, func, name=None):
        self.func = func
        self.__doc__ = getattr(func, '__doc__')
        self.name = name or func.__name__

    def __get__(self, instance, type=None):
        if instance is None:
            return self
        res = instance.__dict__[self.name] = self.func(instance)
        return res


class JsonRequest(object):
    @cached_property
    def json(self):
        res = self.execute()
        content_type = res.headers.get('content-type', '')
        if not content_type.startswith('application/json'):
            raise UnexpectedResponse(self, res)
        return json.loads(res.data)

    def json_body(self, data):
        return (self.with_headers({'Content-Type': 'application/json'})
                .replace(body=json.dumps(data)))

    def put_json(self, data):
        return self.json_body(data).replace(method="PUT")


class Urllib3Request(object):
    logger = logging

    @property
    def response(self):
        res = self.execute()
        if res.status // 100 != 2:
            raise UnexpectedResponse(self, res)
        return res

    def execute(self, **kwargs):
        self.logger.info('%s:%s' % (self.method, self.get_url()))
        url = self.get_url()
        return self.http.urlopen(self.method, url, headers=self.headers,
                                 body=self.body, **kwargs)



    @property
    def http(self):
        cls = type(self)
        if not hasattr(cls, '_http'):
            cls._http = urllib3.PoolManager()
        return cls._http


class Request(RequestURL, Urllib3Request, JsonRequest):
    pass


from_url = Request.from_url


__all__ = ('Request', 'RequestURL', 'JsonRequest', 'Urllib3Request',
           'RequestTuple', 'UnexpectedResponse')
