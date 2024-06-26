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

import pytest
import gevent
from gevent import pywsgi

from volttron.platform import get_services_core
from volttrontesting.utils.utils import get_rand_http_address

from volttron.platform.agent.known_identities import CONFIGURATION_STORE, PLATFORM_DRIVER

server_addr = get_rand_http_address()
no_scheme = server_addr[7:]
ip, port = no_scheme.split(':')
point = b'forty two'

driver_config_dict_string = """{
    "driver_config": {"device_address": "%s"},
    "driver_type": "restful",
    "registry_config": "config://restful.csv",
    "interval": 20,
    "timezone": "UTC"
}""" % server_addr

restful_csv_string = """Point Name,Volttron Point Name,Units,Writable,Notes,Default
test_point,test_point,Units,True,Test point,forty two"""


# return the global point value no matter what is requested
def handle(env, start_response):
    global point

    if env['REQUEST_METHOD'] == 'POST':
        data = env['wsgi.input']
        length = int(env['CONTENT_LENGTH'])
        point = data.read(length)

    start_response('200 OK', [('Content-Type', 'text/html')])
    return [point]


@pytest.fixture(scope='module')
def agent(request, volttron_instance):
    agent = volttron_instance.build_agent()
    # Clean out platform driver configurations.
    capabilities = {'edit_config_store': {'identity': PLATFORM_DRIVER}}
    volttron_instance.add_capabilities(agent.core.publickey, capabilities)
    agent.vip.rpc.call(CONFIGURATION_STORE,
                       'delete_store',
                       PLATFORM_DRIVER).get(timeout=10)

    # Add test configurations.
    agent.vip.rpc.call(CONFIGURATION_STORE,
                       'set_config',
                       PLATFORM_DRIVER,
                       "devices/campus/building/unit",
                       driver_config_dict_string,
                       "json").get(timeout=10)

    agent.vip.rpc.call(CONFIGURATION_STORE,
                       'set_config',
                       PLATFORM_DRIVER,
                       "restful.csv",
                       restful_csv_string,
                       "csv").get(timeout=10)

    platform_uuid = volttron_instance.install_agent(
        agent_dir=get_services_core("PlatformDriverAgent"),
        config_file={},
        start=True)
    print("agent id: ", platform_uuid)
    gevent.sleep(2)  # wait for the agent to start and start the devices

    server = pywsgi.WSGIServer((ip, int(port)), handle)
    server.start()

    def stop():
        volttron_instance.stop_agent(platform_uuid)
        agent.core.stop()
        server.stop()

    request.addfinalizer(stop)
    return agent


def test_restful_get(agent):
    point = agent.vip.rpc.call(PLATFORM_DRIVER,
                               'get_point',
                               'campus/building/unit',
                               'test_point').get(timeout=10)

    assert point == 'forty two'


def test_restful_set(agent):
    # set point
    point = agent.vip.rpc.call(PLATFORM_DRIVER,
                               'set_point',
                               'campus/building/unit',
                               'test_point',
                               '42').get(timeout=10)
    assert point == '42'

    # get point
    point = agent.vip.rpc.call(PLATFORM_DRIVER,
                               'get_point',
                               'campus/building/unit',
                               'test_point').get(timeout=10)
    assert point == '42'


def test_restful_revert(agent):
    # set point
    point = agent.vip.rpc.call(PLATFORM_DRIVER,
                               'set_point',
                               'campus/building/unit',
                               'test_point',
                               '42').get(timeout=10)
    assert point == '42'

    # revert point
    agent.vip.rpc.call(PLATFORM_DRIVER,
                       'revert_point',
                       'campus/building/unit',
                       'test_point').get(timeout=10)

    # get point
    point = agent.vip.rpc.call(PLATFORM_DRIVER,
                               'get_point',
                               'campus/building/unit',
                               'test_point').get(timeout=10)
    assert point == 'forty two'
