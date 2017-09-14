OptoReader
==========
Receive and process streaming data (via UDP) from the Opto. This block will launch a UDP server that the Opto will send it's streaming packets to. Then, based on its configuration, the block will notify signals corresponding to data points within the streaming packet. Currently, the block will **not** notify the Opto of where to stream its data. Therefore, the Opto will most likely have to be configured to point its streaming target to the server launched by this block.

Properties
----------
- **collect**: The optional buffering period for high volumes. See the [Collector Mixin](https://github.com/niolabs/nio/blob/master/nio/block/mixins/collector/collector.py) for more details
- **host**: IP Address to bind the host UDP server to
- **opto_inputs**: A list of inputs to include in the resulting signal. **title**: The key on the resulting signal to place this input's value on. **type**: The type of value to read. This determines both the conversion function as well as which block of the streaming packet to read from.
- **port**: Integer port number to bind the host UDP server to

Inputs
------
None

Outputs
-------
- **default**: One signal per streamed UDP packet. The signal will contain the attributes defined in the **opto_inputs** configuration and nothing more. Float attributes will be represented as a float type. Integer attributes will be represented as an int type. Digital attributes will be represented as a bool type, True if the digital signal is `HIGH`, False if `LOW`.

Commands
--------
None

Computing the PAC Index
-----------------------
The **index** of each configured Opto input is what tells the block where to retrieve the input's value from the streaming data packet. The streaming data packet format can be found on page 52 of the [Opto22 Manual](http://documents.opto22.com/1465_OptoMMP_Protocol_Guide.pdf). Depending on the **type** of the input, the index will mean different things.
_Note: Indexes are always 0-based, meaning we start counting from 0, not 1_
### Float
If your input is a float, it will be read from the 256 bytes of analog floating point values. Each floating point value conforms to IEEE standards and, as a result, is 4 bytes long. This leaves 64 possible indexes for values.
On the Opto, each module contains 4 points. Therefore, the index is dependent on the module number and the point number on the module you wish to read. The following formula can be used to determine the index (assuming module and point numbers **start counting at 0**):
    INDEX = <MODULE INDEX> * 4 + <POINT INDEX>
So if you were interested in reading the 3rd point (point index `2`) on the 5th module (module index `4`), your resulting index would be `18`.
### Integer
If your input is an integer, the process will be similar to that of a float. The integer type reads from the 256 bytes of counter data and the values are converted as unsigned 32-bit integers. This means, there are 64 possible indexes of integers to read from.
Since these don't correspond to modules, the index should match the index of the counter you wish to read. So if you were interested in reading the 5th counter (counter index `4`), the resulting index would be `4`.
### Digital
Reading digital points means reading only one bit from the 8 bytes of digital points. 8 bytes, with 8 bits per byte, leaves us 256 possible indexes of digital values to read from. However, the first 4 bits are always zero-filled, so in practice, there are only 252 actual digital values streamed.
Each module can send 4 digital values, which will make up half of one byte. However, these digital values appear in reverse order (point 0 is the last one on the stream, point 3 is the first one). Therefore, the following formula can be used to determine the index of a digital point (again, assuming we start counting at 0):
    INDEX = 4 + (<MODULE INDEX> * 4) + (3 - <POINT INDEX>)
The first `+ 4` is there to account for the zero-filled bits at the beginning of the data section. So, if you were interested in reading the digital value from the 2nd point (point index `1`) on the 8th module (module index `7`), the resulting index would be `34`.

Dependencies
------------
None

OptoWriter
==========
 A block for connecting to and writing to the Opto22 PAC 

Properties
----------
- **address**: Address to send data to.
- **host**: IP address of the Opto Host.
- **port**: Integer port number of the Opto Host.
- **prefix**: Memory Map Hex Prefix
- **suffix**: Memory Map Hex Suffix
- **timeout**: Timeout for connection to the Opto Host.
- **write**: Data to write to the Opto Host.

Inputs
------
- **default**: Any list of signals.

Outputs
-------
None

Commands
--------
None

Dependencies
------------
None
