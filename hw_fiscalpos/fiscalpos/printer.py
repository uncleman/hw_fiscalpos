#!/usr/bin/python

import serial
import usb.core
import usb.util

from fiscalpos import *
from exceptions import *
from time import sleep

class Usb(Fiscalpos):
    """ Define USB printer """

    def __init__(self, idVendor, idProduct, timeout=0,interface=0, in_ep=None, out_ep=None):
        """
        @param idVendor  : Vendor ID
        @param idProduct : Product ID
        @param interface : USB device interface
        @param in_ep     : Input end point
        @param out_ep    : Output end point
        """

        self.idVendor  = idVendor
        self.idProduct = idProduct
        self.interface = interface
        self.in_ep     = in_ep
        self.out_ep    = out_ep
        self.counter   = 0
        self.open()

    def open(self):
        """ Search device on USB tree and set is as fiscalpos device """
        
        self.device = usb.core.find(idVendor=self.idVendor, idProduct=self.idProduct)
        if self.device is None:
            raise NoDeviceError()
        try:
            if self.device.is_kernel_driver_active(self.interface):
                self.device.detach_kernel_driver(self.interface) 
            self.device.set_configuration()
            usb.util.claim_interface(self.device, self.interface)

            cfg = self.device.get_active_configuration()
            intf = cfg[(0,0)] # first interface
            if self.in_ep is None:
                # Attempt to detect IN/OUT endpoint addresses
                try:
                    is_IN = lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN
                    is_OUT = lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT
                    endpoint_in = usb.util.find_descriptor(intf, custom_match=is_IN)
                    endpoint_out = usb.util.find_descriptor(intf, custom_match=is_OUT)
                    self.in_ep = endpoint_in.bEndpointAddress
                    self.out_ep = endpoint_out.bEndpointAddress
                except usb.core.USBError:
                    # default values for officially supported printers
                    self.in_ep = 0x82
                    self.out_ep = 0x01

        except usb.core.USBError as e:
            raise HandleDeviceError(e)

    def close(self):
        i = 0
        while True:
            try:
                if not self.device.is_kernel_driver_active(self.interface):
                    usb.util.release_interface(self.device, self.interface)
                    self.device.attach_kernel_driver(self.interface)
                    usb.util.dispose_resources(self.device)
                else:
                    self.device = None
                    return True
            except usb.core.USBError as e:
                i += 1
                if i > 10:
                    return False
        
            sleep(0.1)

    def _sendMsg(self, h1, h2, data):
        stx = '\x02'
        cnt = self._getCounterStr()
        iden = 'E'
        msg = cnt + iden + h1 + h2 + data
        cks = str(sum([ord(i) for i in list(msg)]) % 100)
        etx = '\x03'

        raw = stx + msg + cks + etx

        if len(raw) != self.device.write(self.out_ep, raw, timeout=5000):
            raise TicketNotPrinted()
        print '-----> %s' % raw

        print '<----- %s' % self.__extract_status()
        return self.__extract_status()

    def _getCounterStr(self):
        counter = self.counter
        counter += 1
        self.counter = counter
        if (self.counter >= 100):
            self.counter = 1

        return str(self.counter).zfill(2)

    def __extract_status(self):
        maxiterate = 0
        rep = None
        while rep == None:
            maxiterate += 1
            if maxiterate > 10000:
                raise NoStatusError()
            rep = self.device.read(self.in_ep, 64)
        return "".join([chr(c) for c in rep])

    def __del__(self):
        """ Release USB interface """
        if self.device:
            self.close()
        self.device = None



class Serial(Fiscalpos):
    """ Define Serial printer """

    def __init__(self, devfile="/dev/ttyS0", baudrate=9600, bytesize=8, timeout=1):
        """
        @param devfile  : Device file under dev filesystem
        @param baudrate : Baud rate for serial transmission
        @param bytesize : Serial buffer size
        @param timeout  : Read/Write timeout
        """
        self.devfile  = devfile
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.timeout  = timeout
        self.open()


    def open(self):
        """ Setup serial port and set is as fiscalpos device """
        self.device = serial.Serial(port=self.devfile, baudrate=self.baudrate, bytesize=self.bytesize, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=self.timeout, dsrdtr=True)

        if self.device is not None:
            print "Serial printer enabled"
        else:
            print "Unable to open serial printer on: %s" % self.devfile


    def _raw(self, msg):
        """ Print any command sent in raw format """
        self.device.write(msg)


    def __del__(self):
        """ Close Serial interface """
        if self.device is not None:
            self.device.close()

if __name__ == '__main__':

    printer = Usb(0x04b8,0x0201)

    # printer.cashdraw(2)
    # printer.cashdraw(5)

    #printer.printDailyReport()
    printer.displayAdvertismentText('Benvenuti ...')

    # printer.beginNoFiscalReceipt()
    # printer.printNoFiscalData('Test IP Address 192.168.192.192')
    # printer.printNoFiscalData('Test Mac Address 192.168.192.192')
    # printer.endNoFiscalReceipt()
    printer.printAddedHeader('*'*46,1)
    printer.beginFiscalDocument()
    printer.printRecItem('Padelle',2000,1000)
    printer.printRecDiscountPercentItem(500)
    # # printer.printRecItem('Assorbenti', '2000', '1000')
    # # printer.printRecVoidItem()
    printer.printAddedDescription('*'*46, 1)
    printer.printRecPayment(description='Contanti',amount=10000)
    printer.printRecPayment(paymentType=3, index=1, description='Ticket', amount=1000)
    print 'pago con ticket'
    printer.printRecTicketPayment(1000)
    printer.printAddedLine('Arrivederci !!'.center(46),1)

    # printer.printQRCode('      http:\\\\www.infoporto.it')
    printer.endFiscalReceipt()







