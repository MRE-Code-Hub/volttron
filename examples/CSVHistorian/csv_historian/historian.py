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

import csv
import logging
import os
import sys

from volttron.platform.agent import utils
from volttron.platform.agent.base_historian import BaseHistorian


utils.setup_logging()
_log = logging.getLogger(__name__)
__version__ = '1.0.1'


def historian(config_path, **kwargs):
    """
    This method is called by the main method to parse
    the passed config file or configuration dictionary object, validate the
    configuration entries, and create an instance of the CSVHistorian class
    :param config_path: could be a path to a configuration file or can be a dictionary object
    :param kwargs: additional keyword arguments if any
    :return: an instance of :py:class:`CSVHistorian`
    """
    if isinstance(config_path, dict):
        config_dict = config_path
    else:
        config_dict = utils.load_config(config_path)

    output_path = config_dict.get("output", "historian_output.csv")

    return CSVHistorian(output_path=output_path, **kwargs)


class CSVHistorian(BaseHistorian):
    """
    Historian that stores the data into crate tables.
    """

    def __init__(self, output_path="", **kwargs):
        self.output_path = output_path
        self.csv_dict = None
        self.csv_file = None
        self.default_dir = "./data"
        super(CSVHistorian, self).__init__(**kwargs)

    def version(self):
        return __version__

    def publish_to_historian(self, to_publish_list):
        for record in to_publish_list:
            row = dict()
            row["timestamp"] = record["timestamp"]

            row["source"] = record["source"]
            row["topic"] = record["topic"]
            row["value"] = record["value"]

            self.csv_dict.writerow(row)

        self.report_all_handled()
        self.csv_file.flush()

    def historian_setup(self):
        # if the current file doesn't exist, or the path provided doesn't include a directory, use the default dir
        # in <agent dir>/data
        if not (os.path.isfile(self.output_path) or os.path.dirname(self.output_path)):
            if not os.path.isdir(self.default_dir):
                os.mkdir(self.default_dir)
            self.output_path = os.path.join(self.default_dir, self.output_path)

        self.csv_file = open(self.output_path, "w")


        self.csv_dict = csv.DictWriter(self.csv_file, fieldnames=["timestamp", "source", "topic", "value"])
        self.csv_dict.writeheader()
        self.csv_file.flush()


def main(argv=sys.argv):
    """Main method called by the eggsecutable.
    @param argv:
    """
    try:
        utils.vip_main(historian)
    except Exception as e:
        print(e)
        _log.exception('unhandled exception')


if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
