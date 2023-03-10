# Copyright (c) 2023 Canonical Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import socket

import netifaces


def get_fqdn() -> str:
    """Get FQDN of the machine"""
    return socket.getfqdn()


def get_local_ip_by_default_route() -> str:
    """Get IP address of host associated with default gateway"""
    interface = "lo"
    ip = "127.0.0.1"

    # TOCHK: Gathering only IPv4
    if "default" in netifaces.gateways():
        interface = netifaces.gateways()["default"][netifaces.AF_INET][1]

    ip_list = netifaces.ifaddresses(interface)[netifaces.AF_INET]
    if len(ip_list) > 0 and "addr" in ip_list[0]:
        ip = ip_list[0]["addr"]

    return ip
