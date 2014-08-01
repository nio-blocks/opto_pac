Opto-22 PAC
=======

Blocks that can communicate with an [Opto-22 PAC](http://opto22.com)

-   [OptoReader](https://github.com/nio-blocks/opto_pac#OptoReader)
-   [OptoWriter](https://github.com/nio-blocks/opto_pac#OptoWriter)

***

OptoReader
===========

Receive and process streaming data (via UDP) from the Opto.

This block will launch a UDP server that the Opto will send it's streaming packets to. Then, based on its configuration, the block will notify signals corresponding to data points within the streaming packet.

Currently, the block will **not** notify the Opto of where to stream its data. Therefore, the Opto will most likely have to be configured to point its streaming target to the server launched by this block.

Properties
--------------

-   **host**: IP Address to bind the host UDP server to
-   **port**: Integer port number to bind the host UDP server to
-   **collect**: The optional buffering period for high volumes. See the [Collector Mixin](https://github.com/nio-blocks/mixins/tree/master/collector) for more details
-   **opto_inputs**: A list of inputs to include in the resulting signal
  -    **title**: The key on the resulting signal to place this input's value on
  -    **type**: The type of value to read. This determines both the conversion function as well as which block of the streaming packet to read from.
  -    **index**: The index of the streaming data block where this input is. See [Computing the PAC Index](https://github.com/nio-blocks/opto_pac#computing_the_pac_index) for help in figuring out what the index should be.


Dependencies
----------------
None

Commands
----------------
None

Input
-------
None

Output
---------
One signal per streamed UDP packet. The signal will contain the attributes defined in the **opto_inputs** configuration and nothing more.

***

OptoWriter
===========



Properties
--------------


Dependencies
----------------
None

Commands
----------------
None

Input
-------
None

Output
---------
None
