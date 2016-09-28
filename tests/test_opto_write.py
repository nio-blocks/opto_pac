from unittest import skipUnless
from ..opto_write import OptoWriter
from nio.signal.base import Signal
from nio.testing.block_test_case import NIOBlockTestCase
from time import sleep

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

    def test_convert_floats(self):
        """Tests that floats get converted correctly."""
        block = OptoWriter()
        self.assertEqual(block._format_in_hex(0.0), '00000000')
        self.assertEqual(block._format_in_hex(1.0), '3F800000')
        self.assertEqual(block._format_in_hex(1.314), '3FA83127')
        self.assertEqual(block._format_in_hex(2.0), '40000000')

    def test_convert_ints(self):
        """Tests that integers get converted correctly."""
        block = OptoWriter()
        self.assertEqual(block._format_in_hex(0), '00000000')
        self.assertEqual(block._format_in_hex(1), '00000001')
        self.assertEqual(block._format_in_hex(314314), '0004CBCA')

        # can't do negative numbers, UNSIGNED int only
        with self.assertRaises(ValueError):
            block._format_in_hex(-1)

    def test_convert_bools(self):
        """Tests that booleans get converted correctly."""
        block = OptoWriter()
        self.assertEqual(block._format_in_hex(False), '00000000')
        self.assertEqual(block._format_in_hex(True), 'FFFFFFFF')
