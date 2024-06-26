## -*- coding: utf-8 -*- {{{
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

import datetime
import logging
import sys

from volttron.platform.vip.agent import Agent, PubSub
from volttron.platform.agent import utils
from volttron.platform.messaging import headers as headers_mod

utils.setup_logging()
_log = logging.getLogger(__name__)

counter = 0

class TestAgent(Agent):

    def __init__(self, config_path, **kwargs):
        super(TestAgent, self).__init__(**kwargs)

        self.setting1 = 42
        self.default_config = {"setting1": self.setting1}

        self.vip.config.set_default("config", self.default_config)
        self.vip.config.subscribe(self.configure, actions=["NEW", "UPDATE"], pattern="config")

    def configure(self, config_name, action, contents):
        config = self.default_config.copy()
        config.update(contents)

        # make sure config variables are valid
        try:
            self.setting1 = int(config["setting1"])
        except ValueError as e:
            _log.error("ERROR PROCESSING CONFIGURATION: {}".format(e))

    @PubSub.subscribe('pubsub', 'heartbeat/listener')
    def on_heartbeat_topic(self, peer, sender, bus, topic, headers, message):
        global counter
        # Test various RPC calls to the Chargepoint driver.
        counter += 1
        if counter > 1:
            # result = self.set_chargepoint_point('shedState', 0)
            # result = self.get_chargepoint_point('stationMacAddr')
            # result = self.get_chargepoint_point('Lat')
            # result = self.get_chargepoint_point('Long')
            # result = self.set_chargepoint_point('allowedLoad', 10)
            # result = self.set_chargepoint_point('percentShed', 50)
            # result = self.set_chargepoint_point('clearAlarms', True)
            # result = self.get_chargepoint_point('alarmType')
            # result = self.get_chargepoint_point('sessionID')
            result = self.get_chargepoint_point('Status')
            # result = self.get_chargepoint_point('stationRightsProfile')

            now = utils.format_timestamp(datetime.datetime.now())
            # Also publish a test pub/sub message just for kicks.
            result = self.publish_message('test_topic/test_subtopic',
                                          {
                                              headers_mod.DATE: now,
                                              headers_mod.TIMESTAMP: now
                                          },
                                          [{'property_1': 1, 'property_2': 2}, {'property_3': 3, 'property_4': 4}])

            counter = 0

    def get_chargepoint_point(self, point_name):
        return self.vip.rpc.call('platform.driver', 'get_point', 'chargepoint1', point_name).get(timeout=10)

    def set_chargepoint_point(self, point_name, value):
        return self.vip.rpc.call('platform.driver', 'set_point', 'chargepoint1', point_name, value).get(timeout=10)

    def publish_message(self, topic, headers, message):
        return self.vip.pubsub.publish('pubsub', topic, headers=headers, message=message).get(timeout=10)

def main(argv=sys.argv):
    """Main method called by the platform."""
    utils.vip_main(TestAgent)


if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
