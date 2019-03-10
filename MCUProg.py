#! python2
#coding: utf-8
''' 更改记录
'''
import os
import sys
import collections
import ConfigParser

import sip
sip.setapi('QString', 2)
from PyQt4 import QtCore, QtGui, uic

from daplink import coresight, pyDAPAccess

import device


'''
class MCUProg(QtGui.QWidget):
    def __init__(self, parent=None):
        super(MCUProg, self).__init__(parent)
        
        uic.loadUi('MCUProg.ui', self)
'''
from MCUProg_UI import Ui_MCUProg
class MCUProg(QtGui.QWidget, Ui_MCUProg):
    def __init__(self, parent=None):
        super(MCUProg, self).__init__(parent)
        
        self.setupUi(self)

        self.prgInfo.setVisible(False)

        self.initSetting()

        self.daplink = None

        self.tmrDAP = QtCore.QTimer()
        self.tmrDAP.setInterval(100)
        self.tmrDAP.timeout.connect(self.on_tmrDAP_timeout)
        self.tmrDAP.start()

    def initSetting(self):
        if not os.path.exists('setting.ini'):
            open('setting.ini', 'w')
        
        self.conf = ConfigParser.ConfigParser()
        self.conf.read('setting.ini')
        
        if not self.conf.has_section('globals'):
            self.conf.add_section('globals')
            self.conf.set('globals', 'mcu',  '')
            self.conf.set('globals', 'addr', '')
            self.conf.set('globals', 'size', '')
            self.conf.set('globals', 'hexpath', '[]')
        self.cmbHEX.addItems(eval(self.conf.get('globals', 'hexpath')))

        for dev in device.Devices: self.cmbMCU.addItem(dev)
        self.cmbMCU.setCurrentIndex(self.cmbMCU.findText(self.conf.get('globals', 'mcu')))

    @QtCore.pyqtSlot()
    def on_btnErase_clicked(self):
        self.dap = self.openDAP()
        self.dev = device.Devices[self.cmbMCU.currentText()](self.dap)
        self.dev.sect_erase(self.addr, self.size)
        QtGui.QMessageBox.information(self, u'擦除完成', u'        芯片擦除完成        ', QtGui.QMessageBox.Yes)

        self.dap.ap.write32(0xE000ED0C, (0x5FA << 16) | (1 << 2))    # NVIC_SystemReset()
        self.dap.dp.flush()

    @QtCore.pyqtSlot()
    def on_btnWrite_clicked(self):
        if self.cmbHEX.currentText().endswith('.hex'): data = parseHex(self.cmbHEX.currentText())
        else:                                          data = open(self.cmbHEX.currentText(), 'rb').read()

        self.dap = self.openDAP()
        self.dev = device.Devices[self.cmbMCU.currentText()](self.dap)

        self.setEnabled(False)
        self.prgInfo.setVisible(True)
        
        self.threadWrite = ThreadAsync(self.dev.chip_write, self.addr, [ord(x) for x in data])  # 进出文件都是bytes，进出Device都是list
        self.threadWrite.taskFinished.connect(self.on_btnWrite_finished)
        self.threadWrite.start()

    def on_btnWrite_finished(self):
        QtGui.QMessageBox.information(self, u'烧写完成', u'        程序烧写完成        ', QtGui.QMessageBox.Yes)

        self.dap.ap.write32(0xE000ED0C, (0x5FA << 16) | (1 << 2))    # NVIC_SystemReset()
        self.dap.dp.flush()

        self.setEnabled(True)
        self.prgInfo.setVisible(False)

    @QtCore.pyqtSlot()
    def on_btnRead_clicked(self):
        self.dap = self.openDAP()
        self.dev = device.Devices[self.cmbMCU.currentText()](self.dap)

        self.setEnabled(False)
        self.prgInfo.setVisible(True)

        self.RdBuffer = []
        self.threadRead = ThreadAsync(self.dev.chip_read, self.addr, self.size, self.RdBuffer)
        self.threadRead.taskFinished.connect(self.on_btnRead_finished)
        self.threadRead.start()

    def on_btnRead_finished(self):
        path = QtGui.QFileDialog.getSaveFileName(caption=u'将读取到的数据保存到文件', filter=u'程序文件 (*.bin)')
        if path:
            with open(path, 'wb') as f:
                f.write(''.join([chr(x) for x in self.RdBuffer]))

        self.dap.ap.write32(0xE000ED0C, (0x5FA << 16) | (1 << 2))    # NVIC_SystemReset()
        self.dap.dp.flush()
        
        self.setEnabled(True)
        self.prgInfo.setVisible(False)

    def openDAP(self):
        self.daplink.open()

        dp = coresight.dap.DebugPort(self.daplink)
        dp.init()
        dp.power_up_debug()
        dp.set_clock(4000000)

        ap = coresight.ap.AHB_AP(dp, 0)
        ap.init()

        dap = coresight.cortex_m.CortexM(self.daplink, dp, ap)
        dap.readCoreType()

        return dap
    
    def on_tmrDAP_timeout(self):
        ''' 自动检测 DAPLink 的热插拔 '''
        daplinks = pyDAPAccess.DAPAccess.get_connected_devices()
        
        if self.daplink and (daplinks == []):   # daplink被拔下
            try:
                self.daplink.close()
            except Exception as e:
                print e
            finally:
                self.daplink = None
                self.linDAP.clear()

        if not self.daplink and daplinks != []:
            self.daplink = daplinks[0]
            self.linDAP.setText(self.daplink._product_name)

    @property
    def addr(self):
        return int(self.cmbAddr.currentText().split()[0]) * 1024

    @property
    def size(self):
        return int(self.cmbSize.currentText().split()[0]) * 1024

    @QtCore.pyqtSlot(str)
    def on_cmbMCU_currentIndexChanged(self, str):
        dev = device.Devices[self.cmbMCU.currentText()]

        self.cmbAddr.clear()
        self.cmbSize.clear()
        for i in range(dev.CHIP_SIZE//dev.SECT_SIZE):
            if (dev.SECT_SIZE * i) % 1024 == 0:
                self.cmbAddr.addItem('%d K'  %(dev.SECT_SIZE * i    // 1024))
            if (dev.SECT_SIZE * (i+1)) % 1024 == 0:
                self.cmbSize.addItem('%d K' %(dev.SECT_SIZE * (i+1) // 1024))

        self.cmbAddr.setCurrentIndex(self.cmbAddr.findText(self.conf.get('globals', 'addr')))
        self.cmbSize.setCurrentIndex(self.cmbSize.findText(self.conf.get('globals', 'size')))

    @QtCore.pyqtSlot()
    def on_btnHEX_clicked(self):
        hexpath = QtGui.QFileDialog.getOpenFileName(caption=u'程序文件路径', filter=u'程序文件 (*.bin *.hex)',
                                                    directory=self.cmbHEX.currentText(),)
        if hexpath:
            self.cmbHEX.insertItem(0, hexpath)
            self.cmbHEX.setCurrentIndex(0)

    def closeEvent(self, evt):        
        self.conf.set('globals', 'mcu', self.cmbMCU.currentText())
        self.conf.set('globals', 'addr', self.cmbAddr.currentText())
        self.conf.set('globals', 'size', self.cmbSize.currentText())
        
        hexpath = [self.cmbHEX.currentText()] + [self.cmbHEX.itemText(i) for i in range(self.cmbHEX.count())]
        self.conf.set('globals', 'hexpath', list(collections.OrderedDict.fromkeys(hexpath)))    # 保留顺序去重   

        self.conf.write(open('setting.ini', 'w'))


class ThreadAsync(QtCore.QThread):
    taskFinished = QtCore.pyqtSignal()

    def __init__(self, func, *args):
        super(ThreadAsync, self).__init__()
        self.func = func
        self.args = args

    def run(self):
        self.func(*self.args)
        self.taskFinished.emit()


def parseHex(file):
    ''' 解析 .hex 文件，提取出程序代码，没有值的地方填充0xFF '''
    data = ''
    currentAddr = 0
    extSegAddr  = 0     # 扩展段地址
    for line in open(file, 'rb').readlines():
        line = line.strip()
        if len(line) == 0: continue
        
        len_ = int(line[1:3],16)
        addr = int(line[3:7],16) + extSegAddr
        type = int(line[7:9],16)
        if type == 0x00:
            if currentAddr != addr:
                if currentAddr != 0:
                    data += chr(0xFF) * (addr - currentAddr)
                currentAddr = addr
            for i in range(len_):
                data += chr(int(line[9+2*i:11+2*i], 16))
            currentAddr += len_
        elif type == 0x02:
            extSegAddr = int(line[9:9+4], 16) * 16
        elif type == 0x04:
            extSegAddr = int(line[9:9+4], 16) * 65536
    
    return data


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    mcu = MCUProg()
    mcu.show()
    app.exec_()
