import socket
import binascii
import struct
from nio.common.block.base import Block
from nio.common.discovery import Discoverable, DiscoverableType
from nio.metadata.properties.int import IntProperty
from nio.metadata.properties.string import StringProperty
from nio.metadata.properties.expression import ExpressionProperty
from nio.metadata.properties.holder import PropertyHolder


class OptoOutput(PropertyHolder):
    address = ExpressionProperty(default='F0260000', title='Address of Output')
    write = ExpressionProperty(default='FFFFFFFF', title='What to write')


class PACException(Exception):
    pass


@Discoverable(DiscoverableType.block)
class OptoWriter(Block):

    """ A block for connecting to and writing to the Opto22 PAC """

    host = StringProperty(title="Opto Host", default="10.0.0.1")
    port = IntProperty(title="Opto Port", default=2001)
    timeout = IntProperty(title="Connection Timeout", default=5)
    prefix = StringProperty(title="Memory Map Hex Prefix", default="FFFF")
    suffix = StringProperty(title="Memory Map Hex Suffix", default="")

    address = ExpressionProperty(default='F0260000', title='Address of Output')
    write = ExpressionProperty(default='FFFFFFFF', title='What to write')

    def __init__(self):
        super().__init__()
        self._socket = None

    def configure(self, context):
        super().configure(context)
        self._connect_socket()
        if self._socket is None:
            raise ConnectionError(
                "OptoWriter failure connecting to host {}:{}".format(
                    self.host, self.port))

    def process_signals(self, signals):
        for sig in signals:
            try:
                pack = self._build_packet(
                    self.prefix + self.address(sig) + self.suffix,
                    self._format_in_hex(self.write(sig)))
                self._send_packet(pack)
            except PACException as pace:
                self._logger.warning(
                    "Could not build packet for {0} : {1}".format(sig, pace))
            except Exception:
                self._logger.exception(
                    "Error processing signal {0}".format(sig))

    def _format_in_hex(self, val):
        """ Takes a value and smartly convert it into hex, for the Opto.

        This function will perform the following conversions:
            float - convert using 32-bit IEEE standards
            int - convert using 32-bit unsigned integer standards
            bool - FFFFFFFF if True, 00000000 if False
            * (anything else) - return the string

        Args:
            val: A value to convert to hex

        Returns:
            hex (str): An 8-character string containing hex values
        """
        if type(val).__name__ == 'float':
            return binascii.hexlify(
                struct.pack('f', val)[::-1]).decode('utf-8').upper()

        if type(val).__name__ == 'int':
            if val < 0:
                raise ValueError("No negative integers allowed")
            return '{0:08X}'.format(val)

        if type(val).__name__ == 'bool':
            if val:
                return 'F' * 8
            else:
                return '0' * 8

        return val

    def _build_packet(self, address, write):
        """Build a packet to write data to a given memory map address.

        Args:
            address (str): a hex string (6 bytes) representing the full memory
                map address to write to
            write (str): a hex string (4 bytes) representing what to write

        Returns:
            None

        Raises:
            PACException: If the address or write arguments are malformed
        """
        data = b''

        # destination_id - must be 0
        data += b'\x00\x00'

        # tl - transaction label
        data += b'\xf8'

        # tcode/pri - must be 0
        data += b'\x00'

        # source_id
        data += b'\x00\x00'

        # destination offset
        d_off = bytearray.fromhex(address)
        if len(d_off) != 6:
            raise PACException(
                "Destination offset data did not have length 6 : {0}"
                .format(d_off))
        data += d_off

        # quadlet data
        quad_data = bytearray.fromhex(write)
        if len(quad_data) != 4:
            raise PACException(
                "Quadlet data did not have length 4 : {0}".format(quad_data))
        data += quad_data

        return data

    def _connect_socket(self):
        try:
            self._socket = socket.create_connection((self.host, self.port),
                                                    self.timeout)
            self._send_power_up_clear()
        except socket.timeout:
            self._logger.exception(
                "Connection to host {}:{} timed out".format(
                    self.host, self.port))
        except ConnectionRefusedError:
            self._logger.exception(
                "Connection to host {}:{} was refused".format(
                    self.host, self.port))
        except:
            self._logger.exception("Failed to connect")

    def _send_power_up_clear(self):
        """Send the PUC message the PAC needs to receive initially."""
        self._send_packet(self._build_packet("FFFFF0380000", "00000001"))

    def _send_packet(self, packet, catch_exception=True):
        self._logger.debug("Sending packet : {0}".format(packet))
        try:
            self._socket.sendall(packet)
        except Exception:
            if catch_exception:
                self._logger.warning("Error sending packet, reconnecting.",
                                     exc_info=True)
                self._close_socket()
                self._connect_socket()
                self._send_packet(packet, False)

    def _close_socket(self):
        try:
            # Attempt to shut down the socket gracefully
            self._socket.shutdown(socket.SHUT_RDWR)
        finally:
            self._socket.close()

    def stop(self):
        if self._socket:
            self._close_socket()
        super().stop()
