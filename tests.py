# -*- coding: utf-8 -*-
import unittest
from unittest.mock import MagicMock, patch

import ipinfo

from ip2w import (OPENWEATHERMAP_API_BASEURL, application,
                  get_ip_from_wsgi_environ, get_location_by_ip,
                  get_weather_for_location)


class BaseIP2WTestCase(unittest.TestCase):
    ip_addr = "168.80.234.211"
    location = ["-6.2146", "106.8451"]

    wsgi_environ = {
        'wsgi.multiprocess': True,
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': '/ip2w/%s' % ip_addr,
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'QUERY_STRING': '',
        'CONTENT_LENGTH': '',
        'HTTP_USER_AGENT': 'curl/7.29.0',
        'SERVER_NAME': 'server_domain_or_ip',
        'REMOTE_ADDR': '127.0.0.1',
        'wsgi.url_scheme': 'http',
        'SERVER_PORT': '80',
        'uwsgi.node': 'f9991e2cac9e',
        'DOCUMENT_ROOT': '/usr/share/nginx/html',
        'wsgi.input': object(),
        'HTTP_HOST': '127.0.0.1',
        'wsgi.multithread': False,
        'REQUEST_URI': '/ip2w/%s' % ip_addr,
        'HTTP_ACCEPT': '*/*',
        'wsgi.version': (1, 0),
        'wsgi.run_once': False,
        'wsgi.errors': object(),
        'REMOTE_PORT': '45990',
        'REQUEST_SCHEME': 'http',
        'uwsgi.version': '2.0.21',
        'CONTENT_TYPE': '',
        'wsgi.file_wrapper': object(),
    }

    ipinfo_response = {
        "ip": ip_addr,
        "city": "Jakarta",
        "region": "Jakarta",
        "country": "ID",
        "loc": ",".join(location),
        "org": "AS23679 Media Antar Nusa PT.",
        "timezone": "Asia/Jakarta"
    }

    ipinfo_handler = ipinfo.Handler()
    openweathermap_apikey = "442ee845c56948a598120cdbb45f1c9e"

    openweathermap_response = {
        "cod": 200,
        "name": u"Джакарта",
        "sys": {
            "country": "ID",
            "type": 2,
            "id": 2073276,
            "sunrise": 1669674455,
            "sunset": 1669719261,
        },
        "clouds": {
            "all": 49
        },
        "visibility": 10000,
        "weather": [
            {
                "main": "Clouds",
                "id": 802,
                "icon": "03d",
                "description": u"переменная облачность",
            }
        ],
        "coord": {
            "lat": -6.2146, "lon": 106.8451,
        },
        "base": "stations",
        "timezone": 25200,
        "dt": 1669698134,
        "main": {
            "temp": 31.09,
            "temp_max": 31.96,
            "humidity": 65,
            "pressure": 1007,
            "temp_min": 31.09,
            "feels_like": 36.37,
        },
        "id": 1642911,
        "wind": {
            "gust": 8.94,
            "speed": 1.34,
            "deg": 125
        },
    }

    weather_result = {
        "city": "Джакарта",
        "conditions": 'переменная облачность',
        "temp": "+31.09",
    }

    @staticmethod
    def mocked_requests_get(url, params=None, **kwargs):
        response = MagicMock()
        response.url = url
        response.reason = "OK"
        response.status_code = 200
        if OPENWEATHERMAP_API_BASEURL in url:
            response.json.return_value = (
                BaseIP2WTestCase.openweathermap_response
            )
        else:
            response.json.return_value = (
                BaseIP2WTestCase.ipinfo_response
            )
        return response

    def setUp(self):
        self.patcher = patch("ip2w.requests.get", new=self.mocked_requests_get)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()


class GetIPFromRequestURITestCase(BaseIP2WTestCase):
    """ get_ip_from_wsgi_environ() tests """

    def test(self):
        ip = get_ip_from_wsgi_environ(self.wsgi_environ)
        self.assertEqual(ip, self.ip_addr)

    def test_none_if_no_ip(self):
        """ None result is ok """
        self.wsgi_environ["PATH_INFO"] = "/ip2w/"
        ip = get_ip_from_wsgi_environ(self.wsgi_environ)
        self.assertEqual(ip, None)

    def test_value_error_wrong_ip(self):
        self.wsgi_environ["PATH_INFO"] = "/ip2w/abc"
        self.assertRaises(ValueError, get_ip_from_wsgi_environ,
                          self.wsgi_environ)

    def test_value_error_no_path(self):
        self.wsgi_environ.pop("PATH_INFO")
        self.assertRaises(ValueError, get_ip_from_wsgi_environ,
                          self.wsgi_environ)


class GetLocationByIPTestCase(BaseIP2WTestCase):
    """ get_location_by_ip() tests """

    def test(self):
        location = get_location_by_ip(self.ip_addr, self.ipinfo_handler)
        self.assertEqual(location, self.location)

    def test_wrong_loc(self):
        self.ipinfo_response.pop("loc")
        self.assertRaises(RuntimeError, get_location_by_ip, self.ip_addr,
                          self.ipinfo_handler)


class GetWeatherByLocationTestCase(BaseIP2WTestCase):
    """ get_weather_for_location() tests """

    def test(self):
        weather_info = get_weather_for_location(self.location[0],
                                                self.location[1],
                                                self.openweathermap_apikey)

        self.assertEqual(weather_info, self.weather_result)


class ApplicationTestCase(unittest.TestCase):
    """ Test entire application() function with real requests. """

    last_status_str = ""  # type: str
    last_response_headers = []  # type: list

    @staticmethod
    def start_response(status_string, response_headers):
        ApplicationTestCase.last_status_str = status_string
        ApplicationTestCase.last_response_headers = response_headers

    def test(self):
        environ = BaseIP2WTestCase.wsgi_environ
        result = application(environ, self.start_response)
        self.assertTrue(len(self.last_status_str) > 0)
        self.assertTrue(len(self.last_response_headers) > 0)
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) == 1)
