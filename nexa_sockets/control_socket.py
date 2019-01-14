# Based on reverse engineering of the Nexa protocol in the following blog
# http://tech.jolowe.se/home-automation-rf-protocols/

import argparse
import time

import RPi.GPIO as GPIO

parser = argparse.ArgumentParser(description="Program to remotely control Nexa remote 433Mhz sockets")
parser.add_argument('--pin', type=int, required=True, help='Data pin for 433Mhz transceiver')
parser.add_argument('--code', required=True, help='The code packet to send')
parser.add_argument('--onoff', required=True, help='"on" to turn the socket on, "off" to turn off')
parser.add_argument('--socket', type=int, required=True, help='The number of Nexa socket to use (1-3)')
parser.add_argument('--repeats', type=int, default=1, help='Count of repeats')
parser.add_argument('--repeat_delay', type=int, default=1, help='Delay in seconds between repeats')
parsed = parser.parse_args()

PIN = parsed.pin
CODE = parsed.code
ON_OFF = None
SOCKET = parsed.socket
REPEATS = parsed.repeats
REPEAT_DELAY = parsed.repeat_delay

# Nexa controllers repeat the code five times.
CODE_REPEATS = 5
# Length of a single time slot.
T_LENGTH = 250
# Fixed and only allowed length of a code.
CODE_LENGTH = 26

# Validate received arguments.
if PIN is None or PIN < 0:
    raise ValueError('Invalid pin number')
if CODE is None or len(CODE) != CODE_LENGTH:
    raise ValueError('Invalid code. Code has to be exactly 26 bits.')
if SOCKET is None or SOCKET < 1 or SOCKET > 3:
    raise ValueError('Invalid socket. Socket has to be 1-3.')
if REPEAT_DELAY is not None and REPEAT_DELAY <= 0:
    raise ValueError('Repeat delay has to be above 0')
if REPEATS <= 0:
    raise ValueError('Repeats has to be above 0')

if parsed.onoff == 'on':
    ON_OFF = 1
elif parsed.onoff == 'off':
    ON_OFF = 0
else:
    raise ValueError('Invalid onoff, must be "on" or "off"')

# Set pin mode as BCM.
GPIO.setmode(GPIO.BCM)

print('Setting pin {0} as OUTPUT'.format(
    PIN
))
GPIO.setup(PIN, GPIO.OUT, initial=GPIO.LOW)


def _usleep(us):
    """Sleep us microseconds"""
    time.sleep(us / 1000000.0)


def _high(t_units=1):
    """Send high part of message"""
    GPIO.output(PIN, GPIO.HIGH)
    _usleep(T_LENGTH * t_units)


def _low(t_units=1):
    """Send low part of message"""
    GPIO.output(PIN, GPIO.LOW)
    _usleep(T_LENGTH * t_units)


def _send_high():
    """Send high bit"""
    _high(1)
    _low(1)


def _send_low():
    """Send low bit"""
    _high(1)
    _low(5)


def _send_sync():
    """Send sync bit"""
    _high(1)
    _low(10)


def _send_pause():
    """Send pause bit"""
    _high(1)
    _low(40)


def _send_groupcode(on):
    """Send group code bit"""
    if on:
        _send_low()
    else:
        _send_high()


def _send_onoff(on):
    """Send on/off code bit"""
    if on:
        _send_low()
    else:
        _send_high()


def _send_channel():
    # Two high bits signify Nexa device.
    # Other products also use the same protocol.
    _send_high()
    _send_high()


def _send_unit(unit):
    """Send unit number 1-3, which indicates which socket to control"""
    if unit == 1:
        _send_high()
        _send_high()
    elif unit == 2:
        _send_high()
        _send_low()
    elif unit == 3:
        _send_low()
        _send_high()
    else:
        raise ValueError('Invalid unit {0}'.format(
            unit
        ))


def send_code(code, unit, onoff):
    """
    Send the full code with control bits.
    :param code: The 26 bits long unique code which is registered to socket.
    :param unit: Unit to control 1-3.
    :param onoff: 1 to turn unit on, 0 to turn it off.
    """

    print('Sending onoff:{0} to Nexa unit:{1} with code:{2}'.format(
        onoff,
        unit,
        code
    ))

    # Send the code several times.
    for i in range(CODE_REPEATS):
        _send_sync()

        for i in range(len(code)):
            bit = code[i]
            if bit == '1':
                _send_high()
            elif bit == '0':
                _send_low()
            else:
                raise ValueError('Invalid bit in code: {0}, at position {1}'.format(
                    bit,
                    i
                ))

        _send_groupcode(onoff)
        _send_onoff(onoff)
        _send_channel()
        _send_unit(unit)
        _send_pause()

    print('{0} repeats of code sent'.format(
        CODE_REPEATS
    ))


# Send the provided code to provided socket.
for i in range(REPEATS):
    send_code(CODE, SOCKET, ON_OFF)

    if REPEAT_DELAY is not None:
        print('Sleeping {0} seconds'.format(
            REPEAT_DELAY
        ))
        time.sleep(REPEAT_DELAY)

print('Cleaning up')
GPIO.cleanup()

print('Done')
