# MCUProgFast
 MCU programmer using CMSIS-DAP (DAPLink), using Keil MDK's *.FLM Flashing Algorithm

to run this software, you need python2.7, pyqt4, enum34 and a usb backend (hidapi or pywinusb for windows, pyusb for linux, hidapi for mac)

![](https://github.com/XIVN1987/MCUProgFast/blob/master/%E6%88%AA%E5%9B%BE.png)

Note: the software uses the following statement to find the debugger
``` python 
if product_name.find("CMSIS-DAP") < 0:
    # Skip non cmsis-dap HID device
```

FlashAlgo/flash_algo.py is used to parse Keil MDK's *.FLM file and extract code and its runing information into a python dict. And then you can modify the generated code to add new device support.
