#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
# Created: 02/2022
# Author: Michael Marti <micmarti@ethz.ch>

'''
Module docstring
'''
import os
import tiqi_plugin
import socket
import json
import os
import enum

from tiqi_plugin.decorators import Saver
from thorlabs_ell9k_ctrl.driver.ELL9K import ELL9K

WEBPORT = 8001
RPCPORT = 6001

@Saver('settings.json')
class Interface():
    _port = '/dev/ttyUSB0'
    
    def __init__(self):
        self.ELL9K = ELL9K(self._port)
    
    def __repr__(self) -> str:
        return "Thorlabs ELL9K RC"





if __name__ == '__main__':
    interface = Interface()

    tiqi_plugin.run(interface,
                    host='0.0.0.0',
                    enable_rpc=True,
                    web_port=WEBPORT,
                    rpc_port=RPCPORT,
                    css=os.path.join(os.getcwd(), 'custom.css')
                    )
