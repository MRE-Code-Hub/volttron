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

"""
a single pytest case for global platform driver settings.
"""

import pytest
import gevent

from volttron.platform import get_services_core
from volttron.platform.agent.known_identities import PLATFORM_DRIVER
from volttron.platform.vip.agent import Agent
from volttron.platform.messaging import topics
from volttron.platform.agent.utils import parse_timestamp_string

fake_device_config = """
{{
    "driver_config": {{}},
    "registry_config":"config://fake.csv",
    "interval": 1,
    "timezone": "US/Pacific",
    "heart_beat_point": "Heartbeat",
    "driver_type": "fakedriver",
    "group": {group}

}}
"""

platform_driver_config = """
{{
    "driver_scrape_interval": 0.1,
    "group_offset_interval": {interval},
    "publish_breadth_first_all": false,
    "publish_depth_first_all": true,
    "publish_depth_first": false,
    "publish_breadth_first": false
}}
"""

registry_config_string = """Point Name,Volttron Point Name,Units,Units Details,Writable,Starting Value,Type,Notes
Float,Float,F,-100 to 300,TRUE,50,float,CO2 Reading 0.00-2000.0 ppm
FloatNoDefault,FloatNoDefault,F,-100 to 300,TRUE,,float,CO2 Reading 0.00-2000.0 ppm
"""


@pytest.mark.driver
def test_add_remove_drivers(test_agent, subscriber_agent):
    setup_config(test_agent, "config", platform_driver_config, interval=0.5)
    setup_config(test_agent, "devices/fake0_0", fake_device_config, group=0)
    setup_config(test_agent, "devices/fake0_1", fake_device_config, group=0)
    setup_config(test_agent, "devices/fake0_2", fake_device_config, group=0)
    setup_config(test_agent, "devices/fake1_0", fake_device_config, group=1)
    setup_config(test_agent, "devices/fake1_1", fake_device_config, group=1)
    setup_config(test_agent, "devices/fake1_2", fake_device_config, group=1)

    subscriber_agent.reset_results()

    # Give it enough time to publish at least once.
    gevent.sleep(2)

    results = subscriber_agent.get_results()

    assert results["devices/fake0_0/all"] == 0
    assert results["devices/fake0_1/all"] == 1
    assert results["devices/fake0_2/all"] == 2
    assert results["devices/fake1_0/all"] == 5
    assert results["devices/fake1_1/all"] == 6
    assert results["devices/fake1_2/all"] == 7

    remove_config(test_agent, "devices/fake0_1")
    remove_config(test_agent, "devices/fake1_1")

    subscriber_agent.reset_results()

    # Give it enough time to publish at least once.
    gevent.sleep(2)

    results = subscriber_agent.get_results()

    assert results["devices/fake0_0/all"] == 0
    assert results["devices/fake0_2/all"] == 2
    assert results["devices/fake1_0/all"] == 5
    assert results["devices/fake1_2/all"] == 7

    assert "devices/fake0_1/all" not in results
    assert "devices/fake1_1/all" not in results

    setup_config(test_agent, "devices/fake0_1", fake_device_config, group=0)
    setup_config(test_agent, "devices/fake1_1", fake_device_config, group=1)

    subscriber_agent.reset_results()

    # Give it enough time to publish at least once.
    gevent.sleep(2)

    results = subscriber_agent.get_results()

    assert results["devices/fake0_0/all"] == 0
    assert results["devices/fake0_1/all"] == 1
    assert results["devices/fake0_2/all"] == 2
    assert results["devices/fake1_0/all"] == 5
    assert results["devices/fake1_1/all"] == 6
    assert results["devices/fake1_2/all"] == 7


def get_normalized_time_offset(time_string):
    """Parses time_string and returns timeslot of the the value assuming 1 second publish interval
    and 0.1 second driver_scrape_interval."""
    ts = parse_timestamp_string(time_string)
    return ts.microsecond // 100000


class _subscriber_agent(Agent):
    def __init__(self, **kwargs):
        super(_subscriber_agent, self).__init__(**kwargs)
        self.publish_results = {}

    def reset_results(self):
        print("Resetting results")
        self.publish_results.clear()

    def get_results(self):
        return self.publish_results.copy()

    def add_result(self, peer, sender, bus, topic, headers, message):
        print("message published to", topic)
        self.publish_results[topic] = get_normalized_time_offset(headers["TimeStamp"])


@pytest.fixture(scope="module")
def subscriber_agent(volttron_instance):

    agent = volttron_instance.build_agent(
        identity="subscriber_agent", agent_class=_subscriber_agent
    )

    agent.vip.pubsub.subscribe(
        peer="pubsub", prefix=topics.DRIVER_TOPIC_BASE, callback=agent.add_result
    ).get()

    yield agent

    agent.core.stop()


@pytest.fixture(scope="module")
def test_agent(volttron_instance):
    """
    Build a test_agent, PlatformDriverAgent
    """

    # Build a test agent
    md_agent = volttron_instance.build_agent(identity="test_md_agent")
    gevent.sleep(1)

    if volttron_instance.auth_enabled:
        capabilities = {"edit_config_store": {"identity": PLATFORM_DRIVER}}
        volttron_instance.add_capabilities(md_agent.core.publickey, capabilities)

    # Clean out platform driver configurations
    # wait for it to return before adding new config
    md_agent.vip.rpc.call("config.store", "delete_store", PLATFORM_DRIVER).get()

    # Add a fake.csv to the config store
    md_agent.vip.rpc.call(
        "config.store",
        "set_config",
        PLATFORM_DRIVER,
        "fake.csv",
        registry_config_string,
        config_type="csv",
    ).get()

    # install the PlatformDriver
    platform_uuid = volttron_instance.install_agent(
        agent_dir=get_services_core("PlatformDriverAgent"), config_file={}, start=True
    )

    gevent.sleep(10)  # wait for the agent to start and start the devices

    yield md_agent

    volttron_instance.stop_agent(platform_uuid)
    md_agent.core.stop()


def setup_config(test_agent, config_name, config_string, **kwargs):
    config = config_string.format(**kwargs)
    print("Adding", config_name, "to store")
    test_agent.vip.rpc.call(
        "config.store",
        "set_config",
        PLATFORM_DRIVER,
        config_name,
        config,
        config_type="json",
    ).get()


def remove_config(test_agent, config_name):
    print("Removing", config_name, "from store")
    test_agent.vip.rpc.call(
        "config.store", "delete_config", PLATFORM_DRIVER, config_name
    ).get()
