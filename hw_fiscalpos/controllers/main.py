import commands
import logging
import os
import os.path
import subprocess
import json
import time
import traceback

try:
    from ..fiscalpos import *
    from ..fiscalpos.exceptions import *
    from ..fiscalpos.printer import Usb
except ImportError:
    fiscalpos = printer = None

from Queue import Queue
from threading import Thread, Lock

try:
    import usb.core
except ImportError:
    usb = None

from openerp import http

import openerp.addons.hw_proxy.controllers.main as hw_proxy

_logger = logging.getLogger(__name__)

# workaround https://bugs.launchpad.net/openobject-server/+bug/947231
# related to http://bugs.python.org/issue7980
from datetime import datetime

datetime.strptime('2012-01-01', '%Y-%m-%d')


class FiscalposDriver(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.queue = Queue()
        self.lock = Lock()
        self.status = {'status': 'connecting', 'messages': []}

    def connected_usb_devices(self):
        connected = []

        # printers can either define bDeviceClass=7, or they can define one of
        # their interfaces with bInterfaceClass=7. This class checks for both.
        # class FindUsbClass(object):
        #     def __init__(self, usb_class):
        #         self._class = usb_class
        #     def __call__(self, device):
        #         # first, let's check the device
        #         if device.bDeviceClass == self._class:
        #             return True
        #
        #
        #         if (device.idProduct == 0x201):
        #             return True
        #
        #         # transverse all devices and look through their interfaces to
        #         # find a matching class
        #         for cfg in device:
        #             intf = usb.util.find_descriptor(cfg, bInterfaceClass=self._class)
        #
        #             if intf is not None:
        #                 return True
        #
        #
        #
        #         return False

        # printers = usb.core.find(find_all=True, custom_match=FindUsbClass(7))

        # if no printers are found after this step we will take the
        # first epson or star device we can find.
        # epson
        # if not printers:
        #     printers = usb.core.find(find_all=True, idVendor=0x04b8)
        # # star
        # if not printers:
        #     printers = usb.core.find(find_all=True, idVendor=0x0519)
        #
        # for printer in printers:
        printer = usb.core.find(idVendor=0x4b8, idProduct=0x201)
        if (printer is not None):
            try:
                description = usb.util.get_string(printer, printer.iManufacturer) + " " + usb.util.get_string(printer,
                                                                                                              printer.iProduct)
            except Exception as e:
                _logger.error("Can not get printer description: %s" % (e.message or repr(e)))
                description = 'Unknown printer'
            connected.append({
                'vendor': printer.idVendor,
                'product': printer.idProduct,
                'name': description
            })

        return connected

    def lockedstart(self):
        with self.lock:
            if not self.isAlive():
                self.daemon = True
                self.start()

    def get_fiscalpos_printer(self):

        printers = self.connected_usb_devices()
        if len(printers) > 0:
            print_dev = Usb(printers[0]['vendor'], printers[0]['product'])
            self.set_status(
                'connected',
                "Connected to %s (in=0x%02x,out=0x%02x)" % (printers[0]['name'], print_dev.in_ep, print_dev.out_ep)
            )
            return print_dev
        else:
            self.set_status('disconnected', 'Printer Not Found')
            return None

    def get_status(self):
        self.push_task('status')
        return self.status

    def open_cashbox(self, printer):
        printer.cashdraw(2)
        printer.cashdraw(5)

    def set_status(self, status, message=None):
        _logger.info(status + ' : ' + (message or 'no message'))
        if status == self.status['status']:
            if message != None and (len(self.status['messages']) == 0 or message != self.status['messages'][-1]):
                self.status['messages'].append(message)
        else:
            self.status['status'] = status
            if message:
                self.status['messages'] = [message]
            else:
                self.status['messages'] = []

        if status == 'error' and message:
            _logger.error('Fiscal Pos Error: ' + message)
        elif status == 'disconnected' and message:
            _logger.warning('Fiscal Printer Device Disconnected: ' + message)

    def run(self):
        printer = None
        if not fiscalpos:
            _logger.error('FiscalPos cannot initialize, please verify system dependencies.')
            return
        while True:
            try:
                error = True
                timestamp, task, data = self.queue.get(True)

                printer = self.get_fiscalpos_printer()

                if printer == None:
                    if task != 'status':
                        self.queue.put((timestamp, task, data))
                    error = False
                    time.sleep(5)
                    continue
                elif task == 'receipt':
                    if timestamp >= time.time() - 1 * 60 * 60:
                        self.print_receipt_body(printer,data)
                elif task == 'xml_receipt':
                    if timestamp >= time.time() - 1 * 60 * 60:
                        _logger.info('Receipt XML not supported')
                        # printer.receipt(data)
                elif task == 'cashbox':
                    if timestamp >= time.time() - 12:
                        self.open_cashbox(printer)
                elif task == 'printstatus':
                    self.print_status(printer)
                elif task == 'status':
                    pass
                error = False

            except NoDeviceError as e:
                print "No device found %s" % str(e)
            except HandleDeviceError as e:
                print "Impossible to handle the device due to previous error %s" % str(e)
            except TicketNotPrinted as e:
                print "The ticket does not seems to have been fully printed %s" % str(e)
            except NoStatusError as e:
                print "Impossible to get the status of the printer %s" % str(e)
            except Exception as e:
                self.set_status('error', str(e))
                errmsg = str(e) + '\n' + '-' * 60 + '\n' + traceback.format_exc() + '-' * 60 + '\n'
                _logger.error(errmsg);
            finally:
                if error:
                    self.queue.put((timestamp, task, data))
                if printer:
                    printer.close()

    def push_task(self, task, data=None):
        self.lockedstart()
        self.queue.put((time.time(), task, data))

    def print_status(self, eprint):
        localips = ['0.0.0.0', '127.0.0.1', '127.0.1.1']
        hosting_ap = os.system('pgrep hostapd') == 0
        ssid = subprocess.check_output('iwconfig 2>&1 | grep \'ESSID:"\' | sed \'s/.*"\\(.*\\)"/\\1/\'',
                                       shell=True).rstrip()
        mac = subprocess.check_output(
            'ifconfig | grep -B 1 \'inet addr\' | grep -o \'HWaddr .*\' | sed \'s/HWaddr //\'', shell=True).rstrip()
        ips = [c.split(':')[1].split(' ')[0] for c in commands.getoutput("/sbin/ifconfig").split('\n') if
               'inet addr' in c]
        ips = [ip for ip in ips if ip not in localips]

        eprint.beginNoFiscalReceipt()

        if hosting_ap:
            eprint.printNoFiscalData('Wireless network: Posbox ')
        elif ssid:
            eprint.printNoFiscalData('Wireless network: ' + ssid)

        if len(ips) == 0:
            eprint.printNoFiscalData('Wireless network: ' + ssid)
            eprint.printNoFiscalData('ERROR: Could not connect to LAN.')
            eprint.printNoFiscalData('Please check that the PosBox is correctly')
            eprint.printNoFiscalData('connected with a network cable, that the LAN ')
            eprint.printNoFiscalData('is setup with DHCP, and that network')
            eprint.printNoFiscalData('addresses are available')

        elif len(ips) == 1:
            eprint.printNoFiscalData(' ')
            eprint.printNoFiscalData('IP Address: ' + ips[0])
        else:
            eprint.printNoFiscalData('IP Addresses: ')
            for ip in ips:
                eprint.printNoFiscalData(' ' + ip)

        if len(ips) >= 1:
            eprint.printNoFiscalData(' ')
            eprint.printNoFiscalData('MAC Address: ' + mac)
            eprint.printNoFiscalData(' ')
            eprint.printNoFiscalData(' Homepage: http://' + ips[0] + ':8069')

        eprint.endNoFiscalReceipt()

    def print_receipt_body(self, eprint, receipt):

        def check(string):
            return string != True and bool(string) and string.strip()

        def price(amount):
            # return ("{0:."+str(receipt['precision']['price'])+"f}").format(amount)
            return int(amount * (10 ** receipt['precision']['price']))

        def discount(amount):
            # return ("{0:."+str(receipt['precision']['price'])+"f}").format(amount)
            return int(amount * (10 ** receipt['precision']['price']))

        def money(amount):
            return int(amount * (10 ** receipt['precision']['money']))

        def quantity(amount):
            # if math.floor(amount) != amount:
            #     return str(int(amount * (10 ** receipt['precision']['quantity'])))
            # else:
            return int(amount * (10 ** receipt['precision']['quantity']))




        # Receipt Header
        header = []
        if receipt['company']['logo']:
            header.append(receipt['company']['name'])

        if check(receipt['company']['contact_address']):
            header.append(receipt['company']['contact_address'])
        if check(receipt['company']['phone']):
            header.append('Tel:' + receipt['company']['phone'])
        if check(receipt['company']['vat']):
            header.append('VAT:' + receipt['company']['vat'])
        if check(receipt['company']['email']):
            header.append(receipt['company']['email'])
        if check(receipt['company']['website']):
            header.append(receipt['company']['website'])
        if check(receipt['header']):
            header.append(receipt['header'])


        for idx, line in enumerate(header):
            eprint.printAddedHeader(line.center(46), idx+1)

        eprint.beginFiscalReceipt()
        # Orderlines
        for line in receipt['orderlines']:
            if line['discount'] != 0:
                origin_unit_price = round(line['price'] * (1 + line['discount'] / 100.0), 2)
                eprint.printRecItem(line['product_name'], quantity(line['quantity']), price(origin_unit_price))
                eprint.printRecDiscountPercentItem(price(line['discount']))
                # origin_unit_price = round(line['price'] * (1 + line['discount'] / 100.0), 2)
                # total_units_discount_price = price((origin_unit_price - line['price_with_tax'])) * line['quantity']
                # eprint.printRecDiscountItem(line['product_name'],total_units_discount_price)
            else:
                eprint.printRecItem(line['product_name'], quantity(line['quantity']), price(line['price']))

            eprint.printAddedDescription(('-'*38).center(38),'1')
        # Paymentlines
        for line in receipt['paymentlines']:
            if 'ticket' in line['journal'].lower():
              eprint.printRecPayment(paymentType=3,index=1,description=line['journal'],amount=money(line['amount']))
            else:
              eprint.printRecPayment(line['journal'], money(line['amount']))

        addedLines = []

        if check(receipt['cashier']):
            eprint.printAddedLine('Operatore: ' + receipt['cashier'],1)
        if check(receipt['name']):
            eprint.printAddedLine('Ordine: ' + receipt['name'],1)

        eprint.printAddedLine('*** Arrivederci ***'.center(46), 1)


         # if check(receipt['footer']):
            #     eprint.text('\n'+receipt['footer']+'\n\n')
            # eprint.text(receipt['name']+'\n')
            # eprint.text(      str(receipt['date']['date']).zfill(2)
            #             +'/'+ str(receipt['date']['month']+1).zfill(2)
            #             +'/'+ str(receipt['date']['year']).zfill(4)
            #             +' '+ str(receipt['date']['hour']).zfill(2)
            #             +':'+ str(receipt['date']['minute']).zfill(2) )
        eprint.endFiscalReceipt()

driver = FiscalposDriver()

driver.push_task('printstatus')

hw_proxy.drivers['fiscalpos'] = driver

class FiscalposProxy(hw_proxy.Proxy):
    @http.route('/hw_proxy/open_cashbox', type='json', auth='none', cors='*')
    def open_cashbox(self):
        _logger.info('FISCAL POS: OPEN CASHBOX')
        driver.push_task('cashbox')

    @http.route('/hw_proxy/print_fiscal_receipt', type='json', auth='none', cors='*')
    def print_receipt(self, receipt):
        _logger.info('FISCAL POS: PRINT RECEIPT')
        _logger.debug(json.dumps(receipt))
        driver.push_task('receipt', receipt)

    # @http.route('/hw_proxy/print_xml_receipt', type='json', auth='none', cors='*')
    # def print_xml_receipt(self, receipt):
    #     _logger.error('FISCAL POS: PRINT XML RECEIPT')
    #     # _logger.debug(json.dumps(receipt))
    #     raise Exception('XML RECEIPT Not Supported')
    #     # driver.push_task('xml_receipt', receipt)
