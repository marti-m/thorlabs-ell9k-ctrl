import serial
import warnings
import logging
import numpy as np
import time

from typing import Tuple, List, Any, Union
from threading import RLock # not to thread, but just to provide lock context management
from tiqi_plugin import trigger_update

from .instr import cmd
from .status_msg import tags, err

class ELL9K:
    _verbose : bool = False
    _port : str = '/dev/ttyUSB0'
    _sleep_time : float = 10000.0 #us
    
    _filter_list : List[str] = ['filter_1', 'filter_2', 'filter_3', 'filter_4']
    _current_pos_idx : int = 0
    _pos_motor : int = 0
    _pos_idx_max : int = 3
    _current_filter : str = 'filter_1'
    
    _ready : bool = False
    _status : str = 'No status available yet. In start-up'
    _verbose : bool = False
    
    _ui_console : str = ''
    
    def __init__(self, port, verbose=False,  *args, **kwargs):
        self._port = port
        self._verbose = verbose
        
        self._current_pos_idx = 0
        self._current_filter = self._filter_list[self._current_pos_idx]
        
        try:
            self._ser = serial.Serial(self._port, baudrate=9600, parity=serial.PARITY_NONE, stopbits = serial.STOPBITS_ONE, bytesize = 8)
            print("Successfully established connection")
        except serial.SerialException:
            print('Could not open port. Make sure that the device is connected')
        
        self.reset()
        if self._verbose:
            print(self._status)
        
        
        
    def _transmit_bytes(self, addr : str, instr : str, data : str):
        addr = addr.encode()   
        msg = addr + instr
        
    
        # add payload - for the ELL9K this will be only an empty string...
        if data is not None:
            # convert int's to a hex string with trailing zeros
            if isinstance(data, int):
                payload = f"{data:0{8}X}" # requires 32 bits
            else:
                payload = data
                
            msg += payload.encode('utf-8')
                         
        if self._verbose:
            print('TX >>>> ' + f'CMD: {instr}, ADDR: {addr}')
        # send message
        self._ser.write(msg)
    
    def _receive_bytes(self) -> str:
        time.sleep(self._sleep_time / 1e6)
        resp = self._ser.read_until(b'\r\n').decode('utf-8')[:-2]
        
        if self._verbose:
            print('RX <<<< ' + resp)
        return resp
    
    def _parse_response(self, resp : str):
        try:
            addr = resp[0]
            tag = resp[1:3]
            data = resp[3:]
        except:
            self._ui_console = "The received tag was not recognized"
            print("Response did not have right format ADDR [1 byte] - TAG [2 bytes] - DATA [>1 bytes]")
            
        # check if tag is in dictionary
        if tag in tags.keys():
            # translate to more human-readable format
            tag = tags[tag] 
            if tag == 'position':
                # get motor position data and convert to string
                self._pos_motor = int(data, base=16)
                # device is ready from my understanding
                self._status = f'Position: {self._pos_motor}'
                self._ready = True
                self._ui_console = 'no error'
            elif tag == 'status':
                # check if data is a valid error message
                if data in err.keys():
                    msg = err[data]
                    self._status = msg
                    
                    if msg == 'ready':
                        self._ready = True
                        self._ui_console = "no error"
                    else:
                        if self._verbose:
                            print(msg)
                        self._ready = False
                        self._ui_console = msg
                else:
                    self._ui_console = "Return error code was not recognized. Error code: " + data
                    self._ready = False
                    
        else:
            self._ui_console = "The received tag was not recognized"
            if self._verbose:
                print("The received tag was not recognized")
    
    def _get_status(self) -> str:
        self._transmit_bytes(addr='0', instr=cmd['status'], data='')
        resp = self._receive_bytes()
        return self._parse_response(resp)
    
    # check if absolute position is possible!
    def _move_to_pos_abs(self, pos_idx: int):
        pos = pos_idx * 32
        self._transmit_bytes(addr = '0', instr = cmd['move_abs'], data = pos)
        self._get_status()
    
    @property
    def status(self) -> str:
        return self._status
    
    @property
    def console(self) -> str:
        return self._ui_console

    @trigger_update('position')
    @trigger_update('filter_str')
    @trigger_update('status')
    def forward(self):
        if self._verbose:
            print('Called forward')
        if self._ready:
            if self._current_pos_idx + 1 <= self._pos_idx_max:
                self._transmit_bytes(addr = '0', instr = cmd['fw'], data = '')
                self._get_status()
                self._current_pos_idx += 1
                self._current_filter = self._filter_list[self._current_pos_idx]
                time.sleep(self._sleep_time / 1e6)
            else:
                if self._verbose:
                    print("Already at the left most position!")
                self._ui_console = "Already at the left most position!"
        else:
            if self._verbose:
                print("Device is not ready! Check status to get more information.")
            self._ui_console = "Device is not ready! Check status to get more information."
        

    @trigger_update('position')
    @trigger_update('filter_str')
    @trigger_update('status')
    @trigger_update('console')
    def backward(self):
        if self._verbose:
            print('Called backward')
        if self._ready:
            if self._current_pos_idx - 1 >= 0:
                self._transmit_bytes(addr = '0', instr = cmd['bw'], data = '')
                self._get_status()
                self._current_pos_idx += -1
                self._current_filter = self._filter_list[self._current_pos_idx]
                time.sleep(self._sleep_time / 1e6)
            else:
                if self._verbose:
                    print("Already at the right most position!")
                self._ui_console = "Already at the right most position!"
        else:
            if self._verbose:
                print("Device is not ready! Check status to get more information.")
            self._ui_console = "Device is not ready! Check status to get more information."
            

    @trigger_update('filter_str')
    @trigger_update('position')
    @trigger_update('status')
    @trigger_update('console')
    def reset(self):
        if self._verbose:
            print('Called home/reset')
        
        self._transmit_bytes(addr = '0', instr = cmd['home'], data = '')
        self._get_status()
        self._current_pos_idx = 0
        self._current_filter = self._filter_list[self._current_pos_idx]

        
    @trigger_update('status')
    @trigger_update('console')
    def update_status(self):
        self._get_status()

            
    @property
    def position(self) -> int:
        return self._current_pos_idx

    
    @position.setter
    @trigger_update('filter_str')
    @trigger_update('status')
    @trigger_update('console')
    def position(self, pos : int):
        if (pos >= 0 and pos <= self._pos_idx_max):
            self._move_to_pos_abs(pos)
            self._current_pos_idx = pos
            self._current_filter = self._filter_list[self._current_pos_idx]
        else:
            if self._verbose:
                print("Set position out of bounds!")
            self._ui_console = "Set position out of bounds!"
            

    @property
    def filter_str(self) -> str:
        return self._current_filter
    

    @filter_str.setter
    @trigger_update('position')
    @trigger_update('status')
    @trigger_update('console')
    def filter_str(self, filter_name : str):
        pos = -1
        for i, filter_str in enumerate(self._filter_list):
            if filter_name == filter_str:
                pos = i
        if pos == -1:
            if self._verbose:
                print("Filter could not be identified by name. Check for typos")
            self._ui_console = "Filter could not be identified by name. Check for typos"
        else:
            self._move_to_pos_abs(pos)
            self._current_pos_idx = pos
            self._current_filter = self._filter_list[self._current_pos_idx]
    
                
    @property
    def filter_list(self):
        return self._filter_list
    

    @trigger_update('console')
    @trigger_update('filter_str')
    @trigger_update('filter_list')
    def change_filter_name(self, idx: int, new_name : str):
        # check if inputs are valid
        if (idx >= 0 and idx < self._pos_idx_max):
            # set new name while printing old name to console
            old_name = self._filter_list[idx]
            self._filter_list[idx] = new_name
            self._current_filter = self._filter_list[self._current_pos_idx] # this will update the current filter if it is renamed
            self._ui_console = "Successfully changed " + old_name + " to " + self._filter_list[idx]
        else:
            self._ui_console = "Index is out of range!"


    @property
    def port(self) -> str:
        return self._port
    


if __name__ == '__main__':
    
    port = '/dev/ttyUSB0'
    slider = ELL9K(port, verbose = True)
    
    slider.backward()
    
    slider.set_position(4)
    slider.set_position(3)
    slider.backward()
    slider.backward()
    slider.set_filter('filter_3')
    slider.home()
