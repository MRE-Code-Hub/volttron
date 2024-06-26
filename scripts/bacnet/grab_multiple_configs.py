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
from os.path import dirname, join
import os
import errno
import subprocess


def makedirs(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("csv_file", type=argparse.FileType('r'),
                        help="Input CSV file")
arg_parser.add_argument("--use-proxy", action="store_true",
                        help="Use proxy_grab_bacnet_config.py to grab configurations.")
arg_parser.add_argument("--proxy-id", help="Use this VIP identity for the BACnet Proxy instance")
arg_parser.add_argument("--out-directory",
                        help="Output directory.", default=".")
arg_parser.add_argument("--ini", help="BACPypes.ini config file to use")

args = arg_parser.parse_args()

program_name = "proxy_grab_bacnet_config.py" if args.use_proxy else "grab_bacnet_config.py"

program_path = join(dirname(__file__), program_name)

devices_dir = join(args.out_directory, "devices")
registers_dir = join(args.out_directory, "registry_configs")

makedirs(devices_dir)
makedirs(registers_dir)

device_list = csv.DictReader(args.csv_file)

for device in device_list:
    address = device["address"]
    device_id = device["device_id"]

    prog_args = ["python3", program_path]
    prog_args.append(device_id)
    if not args.use_proxy and address:
        prog_args.append("--address")
        prog_args.append(address)
    if args.use_proxy and args.proxy_id:
        prog_args += ['--proxy-id', args.proxy_id]
    prog_args.append("--registry-out-file")
    prog_args.append(join(registers_dir, str(device_id)+".csv"))
    prog_args.append("--driver-out-file")
    prog_args.append(join(devices_dir, str(device_id)))
    if args.ini is not None:
        prog_args.append("--ini")
        prog_args.append(args.ini)

    print("executing command:", " ".join(prog_args))

    subprocess.call(prog_args)
