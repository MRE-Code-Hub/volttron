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

import zmq
import logging

from .green import Socket as GreenSocket
from .rmq_connection import BaseConnection
_log = logging.getLogger(__name__)


class ZMQConnection(BaseConnection):
    """
    Maintains ZMQ socket connection
    """
    def __init__(self, url, identity, instance_name, context):
        super(ZMQConnection, self).__init__(url, identity, instance_name)

        self.socket = None
        self.context = context
        self._identity = identity
        self._logger = logging.getLogger(__name__)
        self._logger.debug("ZMQ connection {}".format(identity))

    def open_connection(self, type):
        if type == zmq.DEALER:
            self.socket = GreenSocket(self.context)
            if self._identity:
                self.socket.identity = self._identity.encode('utf-8')
        else:
            self.socket = zmq.Socket()

    def set_properties(self,flags):
        hwm = flags.get('hwm', 6000)
        self.socket.set_hwm(hwm)
        reconnect_interval = flags.get('reconnect_interval', None)
        if reconnect_interval:
            self.socket.setsockopt(zmq.RECONNECT_IVL, reconnect_interval)

    def connect(self, callback=None):
        _log.debug(f"connecting to url {self._url}")
        _log.debug(f"url type is {type(self._url)}")

        self.socket.connect(self._url)
        if callback:
            callback(True)

    def bind(self):
        pass

    def register(self, handler):
        self._vip_handler = handler

    def send_vip_object(self, message, flags=0, copy=True, track=False):
        self.socket.send_vip_object(message, flags, copy, track)

    def send_vip(self, peer, subsystem, args=None, msg_id: bytes = b'',
                 user=b'', via=None, flags=0, copy=True, track=False):
        self.socket.send_vip(peer, subsystem, args=args, msg_id=msg_id, user=user,
                             via=via, flags=flags, copy=copy, track=track)

    def recv_vip_object(self, flags=0, copy=True, track=False):
        return self.socket.recv_vip_object(flags, copy, track)

    def disconnect(self):
        self.socket.disconnect(self._url)

    def close_connection(self, linger=5):
        """This method closes ZeroMQ socket"""
        self.socket.close(linger)
        _log.debug("********************************************************************")
        _log.debug("Closing connection to ZMQ: {}".format(self._identity))
        _log.debug("********************************************************************")
