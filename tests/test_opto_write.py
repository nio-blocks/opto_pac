from unittest import skipUnless
from ..opto_write import OptoWriter
from nio.common.signal.base import Signal
from nio.util.support.block_test_case import NIOBlockTestCase
from nio.modules.threading import sleep

pac_connected = False


class TestOptoWrite(NIOBlockTestCase):

    @skipUnless(pac_connected, "No PAC Connected")
    def test_write(self):
        """Actually write something to the PAC - it must be connected.

        Note that this test doesn't have any assertions, instead a relay
        on the PAC should toggle on and off every half second, for 5 seconds.
        """
        block = OptoWriter()
        self.configure_block(block, {
            "host": "10.10.1.14",
            "port": 2001,
            "address": "{{$addy}}",
            "log_level": "DEBUG",
            "prefix": "FFFF",
            "suffix": ""
        })
        signals = [
            Signal({"addy": "F0900700"}),  # RELAY ON
            Signal({"addy": "F0900704"})  # RELAY OFF
        ]

        block.start()
        for i in range(10):
            block.process_signals([signals[i % 2]])
            sleep(0.5)
        block.stop()
