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

import sys
import logging
from volttron.platform.agent import utils
from volttron.platform.agent.base_market_agent import MarketAgent
from volttron.platform.agent.base_market_agent.poly_line import PolyLine
from volttron.platform.agent.base_market_agent.point import Point
from volttron.platform.agent.base_market_agent.buy_sell import SELLER

_log = logging.getLogger(__name__)
utils.setup_logging()
__version__ = "0.01"

def electric_meter_agent(config_path, **kwargs):
    """Parses the Electric Meter Agent configuration and returns an instance of
    the agent created using that configuation.

    :param config_path: Path to a configuation file.

    :type config_path: str
    :returns: Market Service Agent
    :rtype: MarketServiceAgent
    """
    _log.debug("Starting SampleElectricMeterAgent")
    try:
        config = utils.load_config(config_path)
    except Exception:
        config = {}

    if not config:
        _log.info("Using Sample Electric Meter Agent defaults for starting configuration.")

    market_name = config.get('market_name', 'electric')

    return SampleElectricMeterAgent(market_name, **kwargs)


class SampleElectricMeterAgent(MarketAgent):
    """
    The SampleElectricMeterAgent serves as a sample of an electric meter that
    sells electricity for a single building at a fixed price.
    """
    def __init__(self, market_name, **kwargs):
        super(SampleElectricMeterAgent, self).__init__(**kwargs)
        self.market_name = market_name
        self.join_market(self.market_name, SELLER, None, self.offer_callback, None, self.price_callback, self.error_callback)

    def offer_callback(self, timestamp, market_name, buyer_seller):
        self.make_offer(market_name, buyer_seller, self.create_supply_curve())

    def create_supply_curve(self):
        supply_curve = PolyLine()
        price = 100
        quantity = 0
        supply_curve.add(Point(price=price, quantity=quantity))
        price = 100
        quantity = 1000
        supply_curve.add(Point(price=price, quantity=quantity))
        return supply_curve

    def price_callback(self, timestamp, market_name, buyer_seller, price, quantity):
        _log.debug("Report cleared price for Market: {} {}, Message: {}".format(market_name, buyer_seller, price, quantity))

    def error_callback(self, timestamp, market_name, buyer_seller, error_code, error_message, aux):
        _log.debug("Report error for Market: {} {}, Code: {}, Message: {}".format(market_name, buyer_seller, error_code, error_message))

def main():
    """Main method called to start the agent."""
    utils.vip_main(electric_meter_agent, version=__version__)


if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
