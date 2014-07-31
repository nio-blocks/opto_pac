import binascii
from enum import Enum
from socketserver import ThreadingMixIn, UDPServer, BaseRequestHandler
from nio.common.block.base import Block
from nio.common.discovery import Discoverable, DiscoverableType
from nio.common.signal.base import Signal
from nio.metadata.properties.int import IntProperty
from nio.metadata.properties.string import StringProperty
from nio.metadata.properties.select import SelectProperty
from nio.metadata.properties.list import ListProperty
from nio.metadata.properties.holder import PropertyHolder
from nio.modules.threading import spawn
from .mixins.collector.collector import Collector


class ThreadedUDPServer(ThreadingMixIn, UDPServer):

    def __init__(self, server_address, handler_class, notifier):
        super().__init__(server_address, handler_class)
        self.notifier = notifier


class OptoDataHandler(BaseRequestHandler):

    """
    This class works similar to the TCP handler class, except that
    self.request consists of a pair of data and client socket, and since
    there is no connection the client address must be given explicitly
    when sending data back via sendto().
    """

    def handle(self):
        data = self.request[0].strip()
        #socket = self.request[1]
        #client_addr = self.client_address[0]

        pack = self._parse_packet(data)
        if pack and len(pack):
            self.server.notifier(*pack)

    def _parse_packet(self, packet):
        floats = []
        ints = []
        digitals = []
        try:
            # Get total packet length
            (packet_len, packet) = self._read_bytes(packet, 2, True)

            # Read zero-filled byte
            (_, packet) = self._read_bytes(packet, 1)

            # get transaction code
            # 0x0A for an isochronous data block (4 bits) and synchronization
            # code for Opto 22 use (4 bits)
            (trans_code, packet) = self._read_bytes(packet, 1)

            (floats, packet) = self._read_floats(packet)
            (ints, packet) = self._read_ints(packet)
            (digitals, packet) = self._read_digitals(packet)

        except IndexError:
            # malformed packet
            print("Uh oh, bad packet")
            print(packet)

        return [floats, ints, digitals]

    def _read_floats(self, packet):
        """ Return 64 floats, converted as 32-bit IEEE floating point"""
        # read 256 bytes of float data, 4 bytes at a time
        floats = []
        for i in range(64):
            (next_float, packet) = self._read_bytes(packet, 4)
            floats.append(self._ieee_bytes_to_float(next_float))
        return (floats, packet)

    def _ieee_bytes_to_float(self, float_bytes):
        sign = float_bytes[0] >> 7
        exp = ((float_bytes[0] & 0x7F) << 1) + (float_bytes[1] >> 7)
        significand = int.from_bytes(float_bytes, byteorder='big') & 0x7FFFFF

        return (-1)**sign * (1 + significand/(2**23)) * (2**(exp - 127))

    def _read_ints(self, packet):
        """ Return 64 integers, converted as unsigned 32-bit ints """
        # read 256 bytes of int data, 4 bytes at a time
        ints = []
        for i in range(64):
            (next_int, packet) = self._read_bytes(packet, 4)
            ints.append(int.from_bytes(next_int, byteorder='big'))
            #print(int.from_bytes(next_int, byteorder='big'))
        return (ints, packet)

    def _read_digitals(self, packet):
        """ Return 64 booleans, representing the binary state of each bit """
        (next_digi, packet) = self._read_bytes(packet, 8)

        # Convert the hex bytes to a binary string (1s and 0s)
        a = binascii.hexlify(next_digi)
        my_bin_str = ''.join('{0:08b}'.format(
            int(x, 16)) for x in (a[i:i+2] for i in range(0, len(a), 2)))

        digitals = [(char == '1') for char in my_bin_str]

        return (digitals, packet)

    def _read_bytes(self, packet, num_bytes, intify=False):
        """Take the first N bytes off a string and optionally parse them.

        Given a packet string, take a specified number of bytes from the
        beginning of the string. Returns a tuple containing the stripped off
        bytes and the remainder of the original string.

        Args:
            packet (str): The string packet to read from
            num_bytes (int): How many bytes to read
            intify (bool): Whether to convert the read bytes to an integer
                (defaults to False)

        Returns:
            (val, remain) (tuple): val contains the read value, remain contains
                anything remaining on the string afterwards.

        Raises:
            IndexError: If the number of bytes to read is greater than the
                length of the packet.
        """
        if num_bytes > len(packet):
            raise IndexError

        obj = packet[:num_bytes]
        new_pack = packet[num_bytes:]

        if intify:
            return (int.from_bytes(obj, byteorder='big'), new_pack)
        else:
            return (obj, new_pack)


class OptoInputType(Enum):
    FLOAT = 0
    INTEGER = 1
    DIGITAL = 2


class OptoInput(PropertyHolder):
    title = StringProperty(default='', title='Name of input')
    index = IntProperty(default=0, title='Index of input')
    type = SelectProperty(
        OptoInputType, default=OptoInputType.FLOAT, title='Input Type')


@Discoverable(DiscoverableType.block)
class OptoReader(Collector, Block):

    """ A block for connecting to and reading from the Opto22 PAC """

    host = StringProperty(title="Listener Host", default="127.0.0.1")
    port = IntProperty(title="Listener Port", default=5005)
    opto_inputs = ListProperty(OptoInput, title="Input Mappings")

    def __init__(self):
        super().__init__()
        self._server = None

    def configure(self, context):
        super().configure(context)
        try:
            self._server = ThreadedUDPServer(
                (self.host, self.port),
                OptoDataHandler,
                self._handle_input)
        except Exception as e:
            self._logger.error(
                "Failed to create server - {0} : {1}".format(
                    type(e).__name__, e))

    def start(self):
        super().start()
        if self._server:
            spawn(self._server.serve_forever)
        else:
            self._logger.warning("Server did not exist, so it was not started")

    def stop(self):
        if self._server:
            self._server.shutdown()
        super().stop()

    def _set_dict_val(self, to_dict, from_list, index, key):
        """Sets a value in a dictionary from a list of values.

        Args:
            to_dict (dict): The dict to write in to
            from_list (list): The list to pull the value from
            index (int): The index in the list to pull the value from
            key (str): The key in the dictionary to insert into

        Returns:
            None: It will set the key in the dictionary

        >>> d = dict()
        >>> _set_dict_val(
                to_dict=d,
                from_list=['a', 'b', 'c'],
                index=2,
                key='name')
        >>> assert d['name'] == 'c'
        """
        if index < len(from_list):
            to_dict[key] = from_list[index]

    def _handle_input(self, floats, ints, digitals):
        """Receives a list of floats and returns dict based on configuration"""
        sig_out = dict()
        source_lists = [floats, ints, digitals]

        for opto_in in self.opto_inputs:
            self._set_dict_val(
                to_dict=sig_out,
                from_list=source_lists[opto_in.type.value],
                index=opto_in.index,
                key=opto_in.title)

        self.notify_signals([Signal(sig_out)])
