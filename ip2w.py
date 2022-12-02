#!/usr/bin/python3
# -*- coding: utf-8 -*-

import json
import logging
import os
import re
from configparser import SafeConfigParser
from http import HTTPStatus

import ipinfo
import requests
from ipinfo.details import Details

DEFAULT_CONFIG_FILE = "ip2w.ini"
OPENWEATHERMAP_API_BASEURL = "https://api.openweathermap.org/data/2.5/weather"

_ipinfo_handler = ipinfo.Handler()
_openweathermap_apikey = None  # type: str | None
_logger = logging.getLogger(__name__)


def configure_from_file(config_file=DEFAULT_CONFIG_FILE):
    # type: (str) -> None
    global _ipinfo_handler, _openweathermap_apikey
    cp = SafeConfigParser()
    cp.read(config_file)

    ipinfo_token = cp.get("tokens", "ipinfo_token", raw=False)  # type: str
    _openweathermap_apikey = cp.get("tokens", "openweathermap_apikey",
                                    raw=False)
    _ipinfo_handler.access_token = ipinfo_token

    level = cp.get("logging", "level")
    filename = cp.get("logging", "filename")

    logging.basicConfig(
        level=level, filename=filename,
        format="[%(levelname)s]:%(asctime)s:[%(name)s]: %(message)s",
    )

    _logger.info("configured from %s", config_file)


def get_ip_from_wsgi_environ(environ):
    # type: (dict) -> str | None
    """ Extracts IP from the WSGI 'environ' dict that is passed to the
    'application' callable.
    """

    path = environ.get("PATH_INFO")
    if path is None:
        raise ValueError("no PATH_INFO in environ")
    m = re.match(r"/ip2w/((\d{1,3}\.){3}\d{1,3})?$", path)
    if m is None:
        raise ValueError("wrong PATH_INFO: %s" % path)
    return m.group(1)


def get_location_by_ip(ip_addr, ipinfo_handler):
    # type: (str | None, ipinfo.Handler) -> list
    """ Performs request to the 'ipinfo' web service to get the location
    info by the IP address. If 'ip_addr' is None - location for the
    current IP will be returned.
    """

    # prepare and send the request to ipinfo
    details = ipinfo_handler.getDetails(ip_addr)  # type: Details

    # process ipinfo response
    location = getattr(details, "loc", "")
    m = re.match(r"\-?\d+\.?\d*,\-?\d+\.?\d*", location)
    if not m:
        raise RuntimeError(
            "Can't get location info from response: %s" % details.all
        )
    return location.split(",")


def get_weather_for_location(latitude, longitude, openweathermap_apikey):
    # type: (str, str, str) -> dict
    """ Retrieves weather info from the 'openweathermap' service for the
    specified geographical coordinates.
    """
    api_call = (
            "%s?lat=%s&lon=%s&appid=%s&units=metric&lang=ru" % (
                OPENWEATHERMAP_API_BASEURL, latitude, longitude,
                openweathermap_apikey
            )
    )
    resp = requests.get(api_call)

    _logger.info("openweathermap response: %s", resp)

    data = resp.json(encoding="utf-8")

    city_name = data.get("name", "")

    temperature = str(data.get("main", {}).get("temp"))
    if not temperature.startswith("-"):
        temperature = "+" + temperature

    conditions = data.get("weather", [{}])[0].get("description", "")

    return {"city": city_name, "temp": temperature, "conditions": conditions}


def make_response(start_response_func, http_status, response_dict=None):
    # type: (callable, HTTPStatus, dict | None) -> list

    status_string = " ".join([str(http_status.value), http_status.name])

    if response_dict is None:
        response_dict = {}
    if http_status != HTTPStatus.OK:
        response_dict["status"] = http_status.value

    response_body = [
        json.dumps(response_dict, ensure_ascii=False).encode(encoding="utf-8")
    ]

    content_length = sum([len(s) for s in response_body])
    response_headers = [
        ('Content-Type', 'application/json'),
        ('Content-Length', str(content_length)),
    ]
    start_response_func(status_string, response_headers)
    return response_body


def application(environ, start_response):
    """ WSGI app main entrypoint """

    global _ipinfo_handler, _openweathermap_apikey

    try:
        configure_from_file(
            config_file=os.getenv("APP_CONFIG", DEFAULT_CONFIG_FILE)
        )
    except Exception:
        _logger.exception("can't finish app configuration")
        return make_response(start_response, HTTPStatus.INTERNAL_SERVER_ERROR,
                             {"reason": "can't finish app configuration"})

    # parse PATH_INFO and get the last IP part
    try:
        ip_addr = get_ip_from_wsgi_environ(environ)
    except Exception:
        err_str = "can't get ip address from request"
        _logger.exception(err_str)
        return make_response(start_response, HTTPStatus.BAD_REQUEST,
                             {"reason": err_str})
    else:
        _logger.debug("got IP address from request: '%s'", ip_addr)

    try:
        location = get_location_by_ip(ip_addr, _ipinfo_handler)  # type: list
    except Exception:
        err_str = "can't get location by IP"
        _logger.exception(err_str)
        return make_response(start_response, HTTPStatus.SERVICE_UNAVAILABLE,
                             {"reason": err_str})
    else:
        _logger.debug("got location from IP address: '%s'", location)

    try:
        weather_info = get_weather_for_location(
            location[0], location[1], _openweathermap_apikey
        )  # type: dict
    except Exception:
        err_str = "can't get weather info by location"
        _logger.exception(err_str)
        return make_response(start_response, HTTPStatus.SERVICE_UNAVAILABLE,
                             {"reason": err_str})
    else:
        _logger.debug("got weather info: '%s'", weather_info)

    return make_response(start_response, HTTPStatus.OK, weather_info)
