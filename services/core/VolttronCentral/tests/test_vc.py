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
from __future__ import annotations
from unittest import mock

import pytest
import os
import yaml
import json
import requests

from volttron.platform.messaging.health import STATUS_GOOD
from volttron.platform.web import DiscoveryInfo
# noinspection PyUnresolvedReferences
from vc_fixtures import vc_instance, vcp_instance, vc_and_vcp_together
from volttrontesting.utils.utils import AgentMock
from volttron.platform import jsonapi, jsonrpc, get_services_core
from volttron.platform.web.websocket import VolttronWebSocket
from volttrontesting.utils.web_utils import get_test_web_env
from volttron.platform.vip.agent import Agent
from services.core.VolttronCentral.volttroncentral.agent import VolttronCentralAgent
import gevent
import grequests


@pytest.fixture
def mock_vc():
    VolttronCentralAgent.__bases__ = (AgentMock.imitate(Agent, VolttronCentralAgent()),)
    vc = VolttronCentralAgent()
    vc._configure("test_config", "NEW", {})
    yield vc


@pytest.fixture
def mock_jsonrpc_env(path="jsonrpc", input_data=None, method="POST"):
    yield get_test_web_env(path, input_data, method=method)


@pytest.fixture
def mock_response(monkeypatch):
    def mock_resp(*args, **kwargs):
        class MockResp:
            def __init__(self):
                mock_args = kwargs['json']
                if mock_args['username'] == 'test' and mock_args['password'] == 'test':
                    self.ok = True
                    self.text = '{"refresh_token": "super_secret_refresh_token", "access_token": "super_secret_access_token"}'
                else:
                    self.ok = False
                    self.text = "invalid username/password"
            def send(self) -> MockResp:
                return self
            @property
            def response(self) -> MockResp:
                return self
        return MockResp()
    monkeypatch.setattr(grequests, "post", mock_resp)


@pytest.mark.vc
def test_jsonrpc_get_authorization(mock_response, mock_vc, mock_jsonrpc_env, monkeypatch):

    mock_claims = {"groups": ["test_admin"]}
    mock_vc.vip.web.configure_mock(**{"get_user_claims.return_value": mock_claims})

    data = jsonrpc.json_method("12345", "get_authorization", {"username": "test", "password": "test"}, None)

    assert len(mock_vc._authenticated_sessions._sessions) == 0

    mock_vc.jsonrpc(mock_jsonrpc_env, data)

    assert len(mock_vc._authenticated_sessions._sessions) == 1

    data = jsonrpc.json_method("12345", "get_authorization", {"username": "test", "password": "nah"}, None)
    response = mock_vc.jsonrpc(mock_jsonrpc_env, data)
    assert response['error']['message'] == "Invalid username/password specified."


@pytest.fixture
def mock_vc_jsonrpc(mock_response, mock_vc, mock_jsonrpc_env, monkeypatch):

    #with mock.patch('volttroncentral.agent.grequests', new=grequests_mock):
    mock_claims = {"groups": ["test_admin"]}
    mock_vc.vip.web.configure_mock(**{"get_user_claims.return_value": mock_claims})
    # mock_vc.vip.web.configure_mock(**{"register_websocket.return_value": VolttronWebSocket})
    data = jsonrpc.json_method("12345", "get_authorization", {"username": "test", "password": "test"}, None)
    mock_vc.jsonrpc(mock_jsonrpc_env, data)
    yield mock_vc


@pytest.fixture
def mock_websocket(mock_vc):
    mock_vc.vip.web.configure_mock(**{"register_websocket.return_value": VolttronWebSocket})
    #.vip.web.configure_mock(**{"register_websocket.return_value": VolttronWebSocket})


@pytest.mark.vc
def test_jsonrpc_is_authorized(mock_vc_jsonrpc, mock_jsonrpc_env):

    data = jsonrpc.json_method("12345", "list_platforms", None, None)
    data['authorization'] = '{"refresh_token": "super_secret_refresh_token", "access_token": "super_secret_access_token"}'
    response = mock_vc_jsonrpc.jsonrpc(mock_jsonrpc_env, data)
    assert len(response['result']) is 0 and type(response['result']) is list


@pytest.mark.vc
def test_jsonrpc_is_unauthorized(mock_vc_jsonrpc, mock_jsonrpc_env):
    data = jsonrpc.json_method("12345", "list_platforms", None, None)
    data['authorization'] = "really_bad_access_token"
    response = mock_vc_jsonrpc.jsonrpc(mock_jsonrpc_env, data)
    assert response['error']['message'] == "Invalid authentication token"


@pytest.mark.vc
def test_installable(volttron_instance_web):
    """
    Test the default configuration file included with the agent
    """
    publish_agent = volttron_instance_web.dynamic_agent

    # config_path = os.path.join(get_services_core("VolttronCentral"), "config")
    # with open(config_path, "r") as config_file:
    #     config_json = yaml.safe_load(config_file)
    # assert isinstance(config_json, dict)

    volttron_instance_web.install_agent(
        agent_dir=get_services_core("VolttronCentral"),
        # config_file=config_json,
        start=True,
        vip_identity="health_test")

    if volttron_instance_web.messagebus == 'rmq':
        gevent.sleep(10)

    assert publish_agent.vip.rpc.call("health_test", "health.get_status").get(timeout=10).get('status') == STATUS_GOOD

#
# def test_platform_was_registered(vc_and_vcp_together):
#
#
# @pytest.mark.vc
# def test_publickey_retrieval(vc_instance, vcp_instance):
#     """ This method tests that the /discovery addresses.
#
#     The discovery now should return the server key for the bus as well as
#     for the volttron.central and platform.agent public keys if they are
#     available.
#
#     Parameters
#     ----------
#     :vc_instance:
#         A dictionary featuring a wrapper and ...
#     :vc_instance:
#         A dictionary featuring a wrapper and ...
#     """
#     vc_wrapper, vc_uuid, jsonrpc = vc_instance
#     pa_wrapper, pa_uuid = vcp_instance
#     gevent.sleep(1)
#
#     vc_info = DiscoveryInfo.request_discovery_info(
#         vc_wrapper.bind_web_address)
#     pa_info = DiscoveryInfo.request_discovery_info(
#         pa_wrapper.bind_web_address)
#
#     assert pa_info.serverkey
#     assert vc_info.serverkey
#     assert pa_info != vc_info.serverkey
#
#
# def onmessage(self, peer, sender, bus, topic, headers, message):
#     print('topic: {} message: {}'.format(topic, message))
#
#
# # @pytest.mark.vc
# # @pytest.mark.parametrize("display_name", [None, "happydays"])
# # def test_register_instance(vc_instance, pa_instance, display_name):
# #     vc_wrapper = vc_instance['wrapper']
# #     pa_wrapper = pa_instance['wrapper']
# #
# #     validate_instances(vc_wrapper, pa_wrapper)
# #
# #     print("connecting to vc instance with vip_adddress: {}".format(
# #         pa_wrapper.vip_address)
# #     )
# #
# #     controlagent = vc_wrapper.build_agent()
# #     controlagent.vip.pubsub.subscribe('', onmessage)
# #     controlagent.vip.rpc.call(
# #         'volttron.central', pa_wrapper.bind_web_address).get(timeout=5)
# #
# #     gevent.sleep(20)
#
#     # res = requests.get(pa_wrapper.bind_web_address+"/discovery/")
#     #
#     # assert res.ok
#     #
#     # viptcp = "{vip_address}?serverkey={serverkey}&secretkey
#     #
#     # authfile = os.path.join(vc_wrapper.volttron_home, "auth.json")
#     # with open(authfile) as f:
#     #     print("vc authfile: {}".format(f.read()))
#     #
#     # tf = tempfile.NamedTemporaryFile()
#     # paks = KeyStore(tf.name)
#     # paks.generate()  #needed because using a temp file!!!!
#     # print('Checking peers on pa using:\nserverkey: {}\npublickey: {}\n'
#     #       'secretkey: {}'.format(
#     #     pa_wrapper.publickey,
#     #     paks.public(),
#     #     paks.secret()
#     # ))
#     # paagent = pa_wrapper.build_agent(serverkey=pa_wrapper.publickey,
#     #                                  publickey=paks.public(),
#     #                                  secretkey=paks.secret())
#     # peers = paagent.vip.peerlist().get(timeout=3)
#     # assert "platform.agent" in peers
#     # paagent.core.stop()
#     # del paagent
#     #
#     # tf = tempfile.NamedTemporaryFile()
#     # ks = KeyStore(tf.name)
#     # ks.generate()  #needed because using a temp file!!!!!
#     # print('Checking peers on vc using:\nserverkey: {}\npublickey: {}\n'
#     #       'secretkey: {}'.format(
#     #     vc_wrapper.publickey,
#     #     ks.public(),
#     #     ks.secret()
#     # ))
#     #
#     # # Create an agent to use for calling rpc methods on volttron.central.
#     # controlagent = vc_wrapper.build_agent(serverkey=vc_wrapper.publickey,
#     #                                       publickey=ks.public(),
#     #                                       secretkey=ks.secret())
#     # plist = controlagent.vip.peerlist().get(timeout=2)
#     # assert "volttron.central" in plist
#     #
#     # print('Attempting to manage platform now.')
#     # print('display_name is now: ', display_name)
#     # dct = dict(peer="volttron.central", method="register_instance",
#     #                                     discovery_address=pa_wrapper.bind_web_address,
#     #                                     display_name=display_name)
#     # print(jsonapi.dumps(dct))
#     # if display_name:
#     #     retval = controlagent.vip.rpc.call("volttron.central", "register_instance",
#     #                                     discovery_address=pa_wrapper.bind_web_address,
#     #                                     display_name=display_name).get(timeout=10)
#     # else:
#     #
#     #     retval = controlagent.vip.rpc.call("volttron.central", "register_instance",
#     #                                     discovery_address=pa_wrapper.bind_web_address).get(timeout=10)
#     #
#     # assert retval
#     # if display_name:
#     #     assert display_name == retval['display_name']
#     # else:
#     #     assert pa_wrapper.bind_web_address == retval['display_name']
#     # assert retval['success']
#     #
#     # print('Testing that we now have a single entry in the platform_details')
#     # retval = controlagent.vip.rpc.call("volttron.central",
#     #                                    "list_platform_details").get(timeout=10)
#     # print("From vc list_platform_details: {}".format(retval))
#     #
#     # assert len(retval) == 1
#     # assert 'hushpuppy' == retval[0]['display_name']
#     # assert retval[0]['vip_address']
#     # assert not retval[0]['tags']
#     # assert retval[0]['serverkey']
#     #
#     # controlagent.core.stop()
#
#     # # build agent to interact with the vc agent on the vc_wrapper instance.
#     # #agent = vc_wrapper.build_agent(**params)
#     # # serverkey=vc_wrapper.publickey,
#     # #                                publickey=ks.public(),
#     # #                                secretkey=ks.secret())
#     # with open(authfile) as f:
#     #     print("vc authfile: {}".format(f.read()))
#     # peers = agent.vip.peerlist().get(timeout=2)
#     # assert "volttron.central" in peers
#
