#!/usr/bin/env python
# encoding: utf-8
"""
    __init__.py
    @author yf
    @version
    Copyright (c) 2013 yufeng All rights reserved.
"""
import tornado.web
import tornado.web, hmac, hashlib, datetime, json, time #, functools, urllib, os
from tornado.escape import json_decode
from tornado import escape
import decimal
import logging as l
import urllib, urllib2, json, hashlib

def _default(obj):
    if isinstance(obj, datetime.datetime):
        return obj.strftime('%Y-%m-%dT%H:%M:%S')
    elif isinstance(obj, datetime.date):
        return obj.strftime('%Y-%m-%d')
    elif isinstance(obj, decimal.Decimal):
        return str(obj)
    else:
        return obj

class base(tornado.web.RequestHandler):
    @property
    def db(self):
        return self.application.db

    def get_current_user(self):
        uid = self.get_secure_cookie("u")
        u = self.db.user(id=uid).one()
        if u:
            return self.get_secure_cookie("u")
        return None

    def write(self, chunk):
        if isinstance(chunk, dict):
            cb = self.get_argument("callback", None)
            if cb is not None:
                super(base, self).write(cb + '(' + json.dumps(chunk) + ')')
                self.set_header('Content-Type', 'application/javascript')
            else:
                chunk = json.dumps(chunk, default=_default).replace('</', "<\\/")
                self.set_header("Content-Type", "application/json; charset=UTF-8")
                chunk = escape.utf8(chunk)
                self._write_buffer.append(chunk)
        else:
            super(base, self).write(chunk)

    def hour(self, h=1):
        cur = datetime.datetime.now() - datetime.timedelta(minutes=int(h)*60)
        return "%d-%02d-%02d %02d:%02d:%02d" % (cur.year, cur.month, cur.day, cur.hour, cur.minute, cur.second)

    def set_default_headers(self):
        self.set_header('Server', 's')
        # debug CORS
        self.set_header('Access-Control-Allow-Origin', 'http://10.2.24.236:3000')
        self.set_header('Access-Control-Allow-Credentials', 'true')

    def json_decode(self, v):
        r = {}
        for ite in v.split("&"):
            vs = ite.split("=")
            if len(vs) == 2 and tornado.escape.url_unescape(vs[0]) != '_xsrf':
                r[tornado.escape.url_unescape(vs[0])] = tornado.escape.url_unescape(vs[1])
        return r

    @property
    def now(self):
        return datetime.datetime.now()

    def timest(self):
        return time.time()

    def setToken(self):
        url = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=wx872cc0c563eaff04&secret=009600ff4d8cce915f071b1ac202c22f"
        req = urllib2.Request(url)
        res_data = urllib2.urlopen(req)
        res = res_data.read()
        json_acceptable_string = res.replace("'", "\"")
        d = json.loads(json_acceptable_string)
        if d["access_token"] is not None:
            self.application._token = d["access_token"]
        else:
            self.application._token = ""

    def getU(self):
        url = "https://api.weixin.qq.com/cgi-bin/user/info/batchget?access_token=" + self.application._token
        req = urllib2.Request(url)
        res_data = urllib2.urlopen(req)
        res = res_data.read()
        json_acceptable_string = res.replace("'", "\"")
        d = json.loads(json_acceptable_string)
        return d