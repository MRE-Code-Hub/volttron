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



import logging
import weakref

from .base import SubsystemBase
from ..dispatch import Signal
from ..results import ResultsDictionary
from volttron.platform import jsonapi
from zmq import ZMQError
from zmq.green import ENOTSOCK

__all__ = ['PeerList']


_log = logging.getLogger(__name__)


class PeerList(SubsystemBase):
    def __init__(self, core):
        self.core = weakref.ref(core)
        self._results = ResultsDictionary()
        core.register('peerlist', self._handle_subsystem, self._handle_error)
        self.onadd = Signal()
        self.ondrop = Signal()
        self.peers_list = set()

    def list(self):
        connection = self.core().connection
        result = next(self._results)

        try:
            connection.send_vip('',
                                'peerlist',
                                args=['list'],
                                msg_id=result.ident)
        except ZMQError as exc:
            if exc.errno == ENOTSOCK:
                _log.error("Socket send on non socket {}".format(self.core().identity))
        return result

    def add_peer(self, peer, message_bus=None):
        connection = self.core().connection
        result = next(self._results)
        if not message_bus:
            message_bus = self.core().messagebus
        try:
            connection.send_vip('',
                                'peerlist',
                                args=['add', peer, message_bus],
                                msg_id=result.ident)
        except ZMQError as exc:
            if exc.errno == ENOTSOCK:
                _log.error("Socket send on non socket {}".format(self.core().identity))
        return result

    def drop_peer(self, peer, message_bus=None):
        connection = self.core().connection
        result = next(self._results)
        if not message_bus:
            message_bus = self.core().messagebus
        try:
            connection.send_vip('',
                                'peerlist',
                                args=['drop', peer, message_bus],
                                msg_id=result.ident)
        except ZMQError as exc:
            if exc.errno == ENOTSOCK:
                _log.error("Socket send on non socket {}".format(self.core().identity))
        return result

    def list_with_messagebus(self):
        connection = self.core().connection
        result = next(self._results)

        try:
            connection.send_vip('',
                                'peerlist',
                                args=['list_with_messagebus'],
                                msg_id=result.ident)
        except ZMQError as exc:
            if exc.errno == ENOTSOCK:
                _log.error("Socket send on non socket {}".format(self.core().identity))
        return result

    __call__ = list

    def _handle_subsystem(self, message):
        try:
            op = message.args[0]
        except IndexError:
            _log.error('missing peerlist subsystem operation')
            return

        if op in ['add', 'drop']:
            try:
                peer = message.args[1]
            except IndexError:
                _log.error('missing peerlist identity in %s operation', op)
                return
            message_bus = None
            try:
                message_bus = message.args[2]
            except IndexError:
                pass
            # getattr requires a string
            onop = 'on' + op
            if message_bus:
                getattr(self, onop).send(self, peer=peer, message_bus=message_bus)
            else:
                getattr(self, onop).send(self, peer=peer)
            if op == 'add':
                self.peers_list.add(peer)
            else:
                if peer in self.peers_list:
                    self.peers_list.remove(peer)
        elif op == 'listing':
            try:
                result = self._results.pop(message.id)
            except KeyError:
                return

            peers = [arg for arg in message.args[1:]]
            result.set(peers)
            self.peers_list = set(peers)
        elif op == 'listing_with_messagebus':
            try:
                result = self._results.pop(message.id)
            except KeyError:
                return
            result.set(jsonapi.loads(message.args[1]))
        else:
            _log.error('unknown peerlist subsystem operation == {}'.format(op))

    def _handle_error(self, sender, message, error, **kwargs):
        try:
            result = self._results.pop(message.id)
        except KeyError:
            return
        result.set_exception(error)
