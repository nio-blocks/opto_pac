import binascii
from enum import Enum
from socketserver import ThreadingMixIn, UDPServer, BaseRequestHandler
from nio.common.block.base import Block
from nio.common.discovery import Discoverable, DiscoverableType
from nio.common.signal.base import Signal
from nio.metadata.properties.int import IntProperty
from nio.metadata.properties.version import VersionProperty
from nio.metadata.properties.string import StringProperty
from nio.metadata.properties.select import SelectProperty
from nio.metadata.properties.list import ListProperty
from nio.metadata.properties.holder import PropertyHolder
from nio.modules.threading import spawn
from .mixins.collector.collector import Collector

from .opto_data import convert_opto, format_str as opto_format_str
from operator import itemgetter
import math
import itertools


class ThreadedUDPServer(ThreadingMixIn, UDPServer):

    def __init__(self, server_address, handler_class, notifier):
        super().__init__(server_address, handler_class)
        self.notifier = notifier


float_index = 3
int_index = float_index + 64
bool_index = int_index + 64
bin_format = "{:0>8b}".format


class OptoDataHandler(BaseRequestHandler):

    """
    This class works similar to the TCP handler class, except that
    self.request consists of a pair of data and client socket, and since
    there is no connection the client address must be given explicitly
    when sending data back via sendto().
    """

    def handle(self):
        data = self.request[0]

        pack = self._parse_packet(data)
        if pack and len(pack):
            self.server.notifier(*pack)

    def _parse_packet(self, packet):
        data = convert_opto(opto_format_str, packet, expected_len=524)
        floats = data[float_index: int_index]
        ints = data[int_index: bool_index]
        digitals = data[bool_index:]

        # process signals
        isnan = math.isnan
        floats = [None if isnan(f) else f for f in floats]
        digitals = [False if n == '0' else True
                        for n in itertools.chain.from_iterable(map(bin_format, digitals))]

        return [floats, ints, digitals]


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
    version = VersionProperty('1.0.0')

    def __init__(self):
        super().__init__()
        self._server = None

    def configure(self, context):
        super().configure(context)

        # key, dtype, index
        self._selections = tuple((o.title, o.type.value, o.index) for o in self.opto_inputs)

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

    def _handle_input(self, floats, ints, digitals):
        """Receives a list of floats and returns dict based on configuration"""
        sig_out = dict()
        source_lists = [floats, ints, digitals]

        sig_out = {key: source_lists[dtype][index] for (key, dtype, index) in self._selections if index < 64}

        self.notify_signals([Signal(sig_out)])
