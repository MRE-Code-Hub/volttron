# -*- coding: utf-8 -*- {{{
# ===----------------------------------------------------------------------===
#
#                 Component of Eclipse VOLTTRON
#
# ===----------------------------------------------------------------------===
#
# Copyright 2023 Battelle Memorial Institute
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# ===----------------------------------------------------------------------===
# }}}

NOBLOCK = 1
SNDMORE = 2
RCVMORE = 13

POLLIN = 1
POLLOUT = 2

PUB = 1
SUB = 2
DEALER = 5
ROUTER = 6
PULL = 7
PUSH = 8
XPUB = 9

EAGAIN = 11
EINVAL = 22
EHOSTUNREACH = 113
EPROTONOSUPPORT = 93


class ZMQError(Exception):
    pass

class Again(ZMQError):
    pass

class Context:
    def instance(self):
        return Context()


class Poller:
    def register(self, socket, flags=POLLIN|POLLOUT):
        pass

    def poll(self, timeout=None):
        return []


class Socket:
    def __new__(cls, socket_type, context=None):
        return object.__new__(cls, socket_type, context=context)

    def bind(self, addr):
        pass

    def connect(self, addr):
        pass

    def disconnect(self, addr):
        pass

    def close(self, linger=None):
        pass

    @property
    def closed(self):
        return True

    @property
    def rcvmore(self):
        return 0

    @property
    def context(self):
        return Context()

    @property
    def type(self):
        return 0

    @context.setter
    def context(self, value):
        pass

    def poll(self, timeout=None, flags=1):
        return 0

    def send_string(self, u, flags=0, copy=True, encoding='utf-8'):
        pass

    def recv_string(self, flags=0, encoding='utf-8'):
        return ''

    def send_multipart(self, msg_parts, flags=0, copy=True, track=False):
        pass

    def recv_multipart(self, flags=0, copy=True, track=False):
        return []

    def send_json(self, obj, flags=0, **kwargs):
        pass

    def recv_json(self, flags=0, **kwargs):
        return {}

    def getsockopt(self, option):
        return 0

green = __import__('sys').modules[__name__]
