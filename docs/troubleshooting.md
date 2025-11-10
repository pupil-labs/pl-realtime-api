If you are having trouble connecting to your Neon / Pupil Invisible device via the real-time API, consider the following points:

1. Make sure the Companion Device and the computer/device you are using to access the API are connected to the same local network.

2. For discovery the local network must allow [mDNS](<https://en.wikipedia.org/wiki/Multicast_DNS#:~:text=Multicast%20DNS%20(mDNS)%20is%20a,Domain%20Name%20System%20(DNS).>) and [UDP](https://en.wikipedia.org/wiki/User_Datagram_Protocol) traffic. In large public networks this may be prohibited for security reasons.
    - You may still be able to connect to Neon using its IP address. You can find the IP address in the WiFi settings of the phone or in the Network tab.
    - Alternatively, you can circumvent this by running a separate WiFi using the phone's hotspot functionality or a dedicated WiFi router.
