from socketserver import ThreadingMixIn, UDPServer, BaseRequestHandler
from nio.common.block.base import Block
from nio.common.discovery import Discoverable, DiscoverableType
from nio.common.signal.base import Signal
from nio.metadata.properties.int import IntProperty
from nio.metadata.properties.string import StringProperty
from nio.metadata.properties.list import ListProperty
from nio.metadata.properties.timedelta import TimeDeltaProperty
from nio.metadata.properties.holder import PropertyHolder
from nio.modules.threading import spawn, Lock
from nio.modules.scheduler import Job


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
            self.server.notifier(pack)

    def _parse_packet(self, packet):
        floats = []
        try:
            # Get total packet length
            (packet_len, packet) = self._read_bytes(packet, 2, True)

            # Read zero-filled byte
            (_, packet) = self._read_bytes(packet, 1)

            # get transaction code
            # 0x0A for an isochronous data block (4 bits) and synchronization
            # code for Opto 22 use (4 bits)
            (trans_code, packet) = self._read_bytes(packet, 1)

            # read 256 bytes of float data, 4 bytes at a time
            floats = []
            for i in range(64):
                (next_float, packet) = self._read_bytes(packet, 4)
                floats.append(self._ieee_bytes_to_float(next_float))
        except IndexError:
            # malformed packet
            print("Uh oh, bad packet")
            print(packet)

        return floats

    def _ieee_bytes_to_float(self, float_bytes):
        sign = float_bytes[0] >> 7
        exp = ((float_bytes[0] & 0x7F) << 1) + (float_bytes[1] >> 7)
        significand = int.from_bytes(float_bytes, byteorder='big') & 0x7FFFFF

        return (-1)**sign * (1 + significand/(2**23)) * (2**(exp - 127))

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


class OptoInput(PropertyHolder):
    title = StringProperty(default='', title='Name of input')
    index = IntProperty(default=0, title='Index of input')


@Discoverable(DiscoverableType.block)
class OptoPAC(Block):

    """ A block for connecting to the Opto22 PAC """

    host = StringProperty(default="127.0.0.1")
    port = IntProperty(default=5005)
    opto_inputs = ListProperty(OptoInput)
    collect = TimeDeltaProperty(
        title='Collect Timeout',
        default={
            "seconds": 1})

    def __init__(self):
        super().__init__()
        self._server = None
        self._collect_job = None
        self._collect_lock = Lock()
        self._sigs_out = []

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
        self._collect_job = Job(self._notify_floats, self.collect, True)
        if self._server:
            spawn(self._server.serve_forever)
        else:
            self._logger.warning("Server did not exist, so it was not started")

    def stop(self):
        if self._server:
            self._server.shutdown()
        if self._collect_job:
            self._collect_job.cancel()
        super().stop()

    def _handle_input(self, floats):
        """Receives a list of floats and returns dict based on configuration"""
        sig_out = dict()
        for opto_in in self.opto_inputs:
            if opto_in.index < len(floats):
                sig_out[opto_in.title] = floats[opto_in.index]

        with self._collect_lock:
            self._sigs_out.append(Signal(sig_out))

    def _notify_floats(self):
        with self._collect_lock:
            if len(self._sigs_out):
                self.notify_signals(self._sigs_out)
                self._sigs_out = []
