# -*- coding: utf-8 -*-
"""
    test
    ~~~~
    Flask-CORS is a simple extension to Flask allowing you to support cross
    origin resource sharing (CORS) using a simple decorator.

    :copyright: (c) 2014 by Cory Dolphin.
    :license: MIT, see LICENSE for more details.
"""

from tests.base_test import FlaskCorsTestCase, AppConfigTest
from flask import Flask
try:
    # this is how you would normally import
    from flask.ext.cors import *
except:
    # support local usage without installed package
    from flask_cors import *

letters = 'abcdefghijklmnopqrstuvwxyz'  # string.letters is not PY3 compatible

class RouteMap(object):
    def __init__(self):
        self.map = {}

    def add(self, path, methods={}, **kwargs):
        self.map[path] = (methods, kwargs)

    def __iter__(self):
        for path, (methods, cors_kwargs) in self.map.items():
            flask_kwargs = {}
            if methods:
                flask_kwargs['methods'] = methods
            yield (path, flask_kwargs, cors_kwargs)

class OriginsCase(object):
    def get_routes(self):
        routes = RouteMap()
        routes.add('/')
        routes.add('/test_list', origins=['http://foo.com', 'http://bar.com'])
        routes.add('/test_string', origins='http://foo.com')
        routes.add('/test_regex_list', origins=[r".*.example.com", r".*.otherexample.com"])
        routes.add('/test_subdomain_regex', origins=r"http?://\w*\.?example\.com:?\d*/?.*")
        routes.add('/test_regex_mixed_list', origins=["http://example.com", r".*.otherexample.com"])
        return routes

        # return routes
    # RESOURCES = {
    #     '/':[{}],
    #     '/test_list': [{'origins':['http://foo.com', 'http://bar.com']}],
    #     '/test_string': [{'origins':'http://foo.com' }],
    #     '/test_regex_list': [{'origins':[r".*.example.com", r".*.otherexample.com"]}],
    #     '/test_subdomain_regex': [{'origins':r"http?://\w*\.?example\.com:?\d*/?.*"}],
    #     '/test_regex_mixed_list': [{'origins': ["http://example.com", r".*.otherexample.com"]}]
    # }

    def test_wildcard_no_origin(self):
        ''' If there is no Origin header in the request, the
            Access-Control-Allow-Origin header should not be included,
            according to the w3 spec.
        '''
        for resp in self.iter_responses('/'):
            self.assertEqual(resp.headers.get(ACL_ORIGIN), None)

    def test_wildcard_with_origin(self):
        ''' If there is no Origin header in the request, the
            Access-Control-Allow-Origin header should be included, if and only
            if the always_send parameter is `True`, which is the default value.
        '''
        for resp in self.iter_responses('/', origin='http://example.com'):
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.headers.get(ACL_ORIGIN), '*')

    def test_list_serialized(self):
        ''' If there is an Origin header in the request, the
            Access-Control-Allow-Origin header should be echoed.
        '''
        resp = self.get('/test_list', origin='http://foo.com')
        self.assertEqual(resp.headers.get(ACL_ORIGIN), 'http://foo.com')

        resp = self.get('/test_list', origin='http://bar.com')
        self.assertEqual(resp.headers.get(ACL_ORIGIN),'http://bar.com')

    def test_string_serialized(self):
        ''' If there is an Origin header in the request,
            the Access-Control-Allow-Origin header should be echoed back.
        '''
        resp = self.get('/test_string', origin='http://foo.com')
        self.assertEqual(resp.headers.get(ACL_ORIGIN), 'http://foo.com')


    def test_not_matching_origins(self):
        for resp in self.iter_responses('/test_list', origin="http://bazz.com"):
            self.assertFalse(ACL_ORIGIN in resp.headers)

    def test_subdomain_regex(self):
        for sub in letters:
            domain = "http://%s.example.com" % sub
            for resp in self.iter_responses('/test_subdomain_regex', origin=domain):
                self.assertEqual(domain, resp.headers.get(ACL_ORIGIN))

    def test_regex_list(self):
        for parent in 'example.com', 'otherexample.com':
            for sub in letters:
                domain = "http://%s.%s.com" % (sub, parent)
                for resp in self.iter_responses('/test_regex_list', origin=domain):
                    self.assertEqual(domain, resp.headers.get(ACL_ORIGIN))

    def test_regex_mixed_list(self):
        '''
            Tests  the corner case occurs when the send_always setting is True
            and no Origin header in the request, it is not possible to match
            the regular expression(s) to determine the correct
            Access-Control-Allow-Origin header to be returned. Instead, the
            list of origins is serialized, and any strings which seem like
            regular expressions (e.g. are not a '*' and contain either '*'
            or '?') will be skipped.

            Thus, the list of returned Access-Control-Allow-Origin header
            is garaunteed to be 'null', the origin or "*", as per the w3
            http://www.w3.org/TR/cors/#access-control-allow-origin-response-header

        '''
        for sub in letters:
            domain = "http://%s.otherexample.com" % sub
            for resp in self.iter_responses('/test_regex_mixed_list', origin=domain):
                self.assertEqual(domain, resp.headers.get(ACL_ORIGIN))

        resp = self.get('/test_regex_mixed_list', origin="http://example.com")
        self.assertEquals("http://example.com", resp.headers.get(ACL_ORIGIN))

class FlaskCorsDecoratorTestCase():
    def setUp(self):
        self.app = Flask(__name__)
        for path, route_options, cors_options in self.get_routes():

            # Flask checks the name of the function to ensure that iew mappings
            # do not collide. We work around it by generating a new function name
            # for the path
            def function_to_rename():
                return 'STUBBED: %s' % path
            function_to_rename.__name__ = 'route_%s' % path

            wrapped_function =  cross_origin(**cors_options)(function_to_rename)
            self.app.route(path)(wrapped_function)

    def get_app(self):
        return self.app

class FlaskCorsDecoratorConfigTestCase():
    def setUp(self):
        self.apps = {}
        for path, route_options, cors_options in self.get_routes():
            apps[path] = Flask(__name__ + path)
            app = apps[path]
            for k,v in cors_options.items():
                app.config['CORS_'+ k.upper()] = v

            # Flask checks the name of the function to ensure that iew mappings
            # do not collide. We work around it by generating a new function name
            # for the path
            def function_to_rename():
                return 'STUBBED: %s' % path
            function_to_rename.__name__ = 'route_%s' % path

            wrapped_function =  cross_origin()(function_to_rename)
            app.route(path)(wrapped_function)


class OriginsDecoratorTestCase(OriginsCase, FlaskCorsDecoratorTestCase, FlaskCorsTestCase):
    pass

class OriginsDecoratorConfigTestCase(OriginsCase, FlaskCorsDecoratorConfigTestCase, FlaskCorsTestCase):
    pass


# class OriginsAppTestCase(OriginsCase)
#
# class AppConfigOriginsTestCase(AppConfigTest, OriginsTestCase):
#     def __init__(self, *args, **kwargs):
#         super(AppConfigOriginsTestCase, self).__init__(*args, **kwargs)
#
#     def test_wildcard_no_origin(self):
#         @self.app.route('/')
#         @cross_origin()
#         def wildcard():
#             return 'Welcome!'
#
#         super(AppConfigOriginsTestCase, self).test_wildcard_no_origin()
#
#     def test_wildcard_with_origin(self):
#         @self.app.route('/')
#         @cross_origin()
#         def wildcard():
#             return 'Welcome!'
#         super(AppConfigOriginsTestCase, self).test_wildcard_with_origin()
#
#     def test_list_serialized(self):
#         self.app.config['CORS_ORIGINS'] = ["http://foo.com", "http://bar.com"]
#
#         @self.app.route('/test_list')
#         @cross_origin()
#         def test_list():
#             return 'Welcome!'
#
#         super(AppConfigOriginsTestCase, self).test_list_serialized()
#
#     def test_string_serialized(self):
#         self.app.config['CORS_ORIGINS'] = "http://foo.com"
#
#         @self.app.route('/test_string')
#         @cross_origin()
#         def test_string():
#             return 'Welcome!'
#
#         super(AppConfigOriginsTestCase, self).test_string_serialized()
#
#     def test_set_serialized(self):
#         self.app.config['CORS_ORIGINS'] = set(["http://foo.com",
#                                                "http://bar.com"])
#
#         @self.app.route('/test_set')
#         @cross_origin()
#         def test_set():
#             return 'Welcome!'
#
#         super(AppConfigOriginsTestCase, self).test_set_serialized()
#
#     def test_not_matching_origins(self):
#         self.app.config['CORS_ORIGINS'] = ["http://foo.com", "http://bar.com"]
#
#         @self.app.route('/test_list')
#         @cross_origin()
#         def test_list():
#             return 'Welcome!'
#
#         super(AppConfigOriginsTestCase, self).test_not_matching_origins()
#
#     def test_regex_list(self):
#         @self.app.route('/test_regex_list')
#         @cross_origin()
#         def _test_regex_list():
#             return 'Welcome!'
#
#         self.app.config['CORS_ORIGINS'] = [r".*.example.com",
#                                            r".*.otherexample.com"]
#         super(AppConfigOriginsTestCase, self).test_regex_list()
#
#     def test_subdomain_regex(self):
#         self.app.config['CORS_ORIGINS'] = r"http?://\w*\.?example\.com:?\d*/?.*"
#
#         @self.app.route('/test_subdomain_regex')
#         @cross_origin()
#         def _test_subdomain_regex():
#             return ''
#
#         super(AppConfigOriginsTestCase, self).test_subdomain_regex()
#
#     def test_regex_mixed_list(self):
#         self.app.config['CORS_ORIGINS'] = ["http://example.com",
#                                            r".*.otherexample.com"]
#
#         @self.app.route('/test_regex_mixed_list')
#         @cross_origin()
#         def _test_regex_mixed_list():
#             return ''
#
#         super(AppConfigOriginsTestCase, self).test_regex_mixed_list()

if __name__ == "__main__":
    unittest.main()
