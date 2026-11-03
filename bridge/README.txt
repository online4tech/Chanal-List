Online4Tech Bridge
==================

What it is
----------
A small program that runs on your Windows computer and lets the Control Center
web page run install commands on your Enigma2 receiver (through Telnet).
Your browser cannot talk to the receiver by itself, so this program does it.

Requirements
------------
Node.js (one time install): https://nodejs.org  -> click the LTS button.
Nothing else. No npm install, no extra packages.

How to use
----------
1. Extract this ZIP to a folder that you will keep, for example C:\bridge
   (right click the ZIP -> Extract All).
2. Double-click  start-bridge.bat
   A black window opens and says "Online4Tech Bridge is running".
   Keep it open while you use the page.
3. Open the Control Center page, pick a tool, press Install, type the
   receiver IP and press "Run on receiver".

Run it automatically with Windows (optional)
--------------------------------------------
Double-click  install-autostart.bat  once.
The bridge then starts hidden every time Windows starts and you never open
the black window again.
To turn it off: double-click  remove-autostart.bat

Notes
-----
- It only listens on your own computer (127.0.0.1).
- It only accepts requests from the Online4Tech Control Center page.
- It only connects to devices on your home network (192.168.x.x, 10.x.x.x, 172.16-31.x.x).
- Phones and tablets cannot run it. On a phone use the "Manual" tab on the page.
