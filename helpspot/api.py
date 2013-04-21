"""
Python HelpSpot interface

A semi-bare shell of a HelpSpot API.

John P. Speno
speno@macspeno.com
Copyright 2010

Inspired by Python Twitter Tools
http://mike.verdone.ca/twitter/

Usage:

Create a HelpSpot object then call methods on it. Any method you call on
the object will be translated into the corresponding HelpSpot Web Services
API call. For methods with a literal dot ('.') in them, replace the dot
with an underscore in Python. Pass arguments to the remote side as keyword
style arguments from Python.

import helpspot

user = 'you@example.com'
pazz = 'idontknow'
path = 'http://helpdesk.example.com/help'

hs = helpspot.HelpSpot(path, user, pazz)

print hs.version()
print hs.private_version()

hs.private_request_update(xRequest='12345', Custom28='90210')
"""
from __future__ import print_function
import base64

try:
    import urllib2 as urllib
except ImportError:
    # python 3
    import urllib

try:
    from urllib import urlencode
except ImportError:
    # python 3
    from urllib.parse import urlencode

try:
    from urllib2 import HTTPHandler
except ImportError:
    # python 3
    from urllib.request import HTTPHandler

try:
    import json
except ImportError:
    import simplejson as json


_POST_METHODS = [
    'request.create',
    'request.update',
    'forums.createTopic',
    'forums.createPost',
    'private.request.create',
    'private.request.update',
    'private.request.addTimeEvent',
    'private.request.deleteTimeEvent',
    'private.request.merge',
    'private.request.unsubscribe',
]


class HelpSpotError(Exception):
    """
    Exception raised when HelpSpot returns HTTP status code 400.
    The instance varibles are as follows:

        err_mesg - Description of the Error from HelpSpot.
        err_id - Error ID of the Error from HelpSpot.

    This does not handle the error case if either public or private API
    are not enabled.

    """
    def __init__(self, err_mesg='', err_id=0):
        self.err_mesg = err_mesg
        self.err_id = err_id

    def __str__(self):
        return '%s (%s)' % (self.err_mesg, self.err_id)


class HelpSpotHandler(HTTPHandler):
    """
    urllib opener class that handles (most) HelpSpot API errors.
    HelpSpot returns HTTP status code 400 for (most) errors.
    """
    def http_error_400(self, req, fp, code, msg, hdrs):
        errs = json.loads(fp.read())
        try:
            details = errs['error'][0]
            err_mesg = details['description']
            err_id = details['id']
        except IndexError:
            err_mesg = 'Unknown HelpSpot API error'
            err_id = 0
        raise HelpSpotError(err_mesg=err_mesg, err_id=err_id)


class HelpSpotAPI(object):
    """
    A HelpSpot API call. Will implicitly raise HelpSpotError
    on API errors otherwise it will return the unmarshalled
    json ouput from HelpSpot.
    """
    def __init__(self, method, user, password, uri):
        """
        Creates a HelpSpotAPI for a given method.
        """
        self.method = method.replace('_', '.')
        self.user = user
        self.password = password
        s = '%s:%s' % (self.user, self.password)
        self.authz = base64.b64encode(s.encode('utf-8')).rstrip()
        self.uri = uri.rstrip('/') + '/api/index.php?method='
        if self.method in _POST_METHODS:
            self.action = 'POST'
        else:
            self.action = 'GET'

    def __call__(self, **kwargs):
        """
        Calls the remote HelpSpot method on the HelpSpot server.
        """
        uri = '%s%s' % (self.uri, self.method)
        params = urlencode(kwargs)
        if 'GET' == self.action:
            if params:
                uri = '%s&%s' % (uri, params)
            message_body = None
        else:
            message_body = params
        uri = '%s&output=json' % uri

        try:
            req = urllib.Request(uri)
        except AttributeError:
            # python 3
            req = urllib.request.Request(uri)
        # Older Python versions may want to uncomment the following line
        # to prevent the server from keeping the connection open.
        #req.add_header('Connection', 'close')
        if self.method.startswith('private.'):
            req.add_header('Authorization', 'Basic %s' % self.authz)

        try:
            # urllib.urlopen could raise URLError, or HelpSpotError
            r = urllib.urlopen(req, message_body)
        except AttributeError:
            # python 3
            r = urllib.request.urlopen(req, message_body)

        # XXX Detect errors when API not enabled
        return json.loads(r.read())


class HelpSpot(object):
    """
    A wrapper object around the HelpSpotAPI. Any method call on this
    object will create and invoke a HelpSpotAPI object.
    """
    def __init__(self, uri, user, password, debuglevel=0):
        self.uri = uri
        self.user = user
        self.password = password
        try:
            opener = urllib.build_opener(HelpSpotHandler(debuglevel=debuglevel))
            urllib.install_opener(opener)
        except AttributeError:
            opener = urllib.request.build_opener(HelpSpotHandler(debuglevel=debuglevel))
            urllib.request.install_opener(opener)

    def __getattr__(self, key):
        try:
            return object.__getattr__(self, key)
        except AttributeError:
            return HelpSpotAPI(key, self.user, self.password, self.uri)


def main():
    user = sys.argv[1]
    password = sys.argv[2]
    uri = sys.argv[3]
    hs = HelpSpot(user=user, password=password, uri=uri)

    ver1 = hs.version()
    print("version returned", ver1)
    ver2 = hs.private_version()
    print("private.version returned", ver2)
    assert ver1 == ver2


if __name__ == '__main__':
    import sys
    sys.exit(main())
