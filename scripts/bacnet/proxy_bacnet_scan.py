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

import argparse
import csv
import logging
from pprint import pprint

import gevent
from volttron.platform.keystore import KeyStore

from volttron.platform import get_address, get_home
from volttron.platform.vip.agent import Agent, PubSub
from volttron.platform.messaging import topics
from volttron.platform.agent import utils
from volttron.platform.vip.agent import errors


utils.setup_logging()
_log = logging.getLogger(__name__)


class BACnetInteraction(Agent):
    def __init__(self, proxy_id, csv_writer=None, **kwargs):
        super(BACnetInteraction, self).__init__(**kwargs)
        self.proxy_id = proxy_id
        self.csv_writer = csv_writer

    def send_iam(self, low_device_id=None, high_device_id=None, address=None):
        self.vip.rpc.call(self.proxy_id, "who_is",
                          low_device_id=low_device_id,
                          high_device_id=high_device_id,
                          target_address=address).get(timeout=5.0)

    @PubSub.subscribe('pubsub', topics.BACNET_I_AM)
    def iam_handler(self, peer, sender, bus,  topic, headers, message):
        if self.csv_writer is not None:
            self.csv_writer.writerow(message)
        pprint(message)


"""
Simple utility to scrape device registers and write them to a configuration file.
"""


def main():
    # parse the command line arguments
    arg_parser = argparse.ArgumentParser(description=__doc__)

    arg_parser.add_argument("--address",
                            help="Target only device(s) at <address> for request")

    arg_parser.add_argument("--range", type=int, nargs=2, metavar=('LOW', 'HIGH'),
                            help="Lower and upper limit on device ID in results")

    arg_parser.add_argument("--timeout", type=int, metavar='SECONDS',
                            help="Time, in seconds, to wait for responses. Default: %(default)s",
                            default=5)

    arg_parser.add_argument("--proxy-id",
                            help="VIP IDENTITY of the BACnet proxy agent.",
                            default="platform.bacnet_proxy")

    arg_parser.add_argument("--csv-out", dest="csv_out",
                            help="Write results to the CSV file specified.")

    arg_parser.add_argument("--debug", action="store_true",
                            help="Set the logger in debug mode")

    args = arg_parser.parse_args()

    core_logger = logging.getLogger("volttron.platform.vip.agent.core")
    core_logger.setLevel(logging.WARN)
    _log.setLevel(logging.WARN)

    if args.debug:
        _log.setLevel(logging.DEBUG)
        core_logger.setLevel(logging.DEBUG)

    _log.debug("initialization")
    _log.debug("    - args: %r", args)

    csv_writer = None
    csv_file = None

    if args.csv_out is not None:
        csv_file = open(args.csv_out, "w")
        field_names = ["address",
                       "device_id",
                       "max_apdu_length",
                       "segmentation_supported",
                       "vendor_id"]
        csv_writer = csv.DictWriter(csv_file, field_names)
        csv_writer.writeheader()

    keystore = KeyStore()
    agent = BACnetInteraction(args.proxy_id,
                              csv_writer=csv_writer,
                              address=get_address(),
                              volttron_home=get_home(),
                              publickey=keystore.public,
                              secretkey=keystore.secret,
                              enable_store=False)

    event = gevent.event.Event()
    gevent.spawn(agent.core.run, event)
    event.wait()

    kwargs = {'address': args.address}

    if args.range is not None:
        kwargs['low_device_id'] = int(args.range[0])
        kwargs['high_device_id'] = int(args.range[1])

    try:
        agent.send_iam(**kwargs)
    except errors.Unreachable:
        _log.error("There is no BACnet proxy Agent running on the platform with the VIP IDENTITY {}".format(
            args.proxy_id))
    else:
        gevent.sleep(args.timeout)
    finally:
        if csv_file is not None:
            csv_file.close()


try:
    main()
except Exception as e:
    _log.exception("an error has occurred: %s".format(repr(e)))
