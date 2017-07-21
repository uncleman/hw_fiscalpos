#### Description


This odoo module is a modified version of hw_escpos to support the following fiscal printer FP-81 II with firmware >= 3.008


#### Installation

###### Requirements:
  * posbox
  * odoo server

###### What to do on posbox
* unzip/copy hw_fiscalpos dir into /home/pi/odoo/addons directory
* change the fs on posbox as writable `sudo mount -o remount,rw /root_bypass_ramdisks`
* edit /root_bypass_ramdisks/etc/init.d/odoo andreplace hw_escopos with hw_fiscalpos

###### What to do on point_of_sale addons
* edit point_of_sale/static/src/js/chrome.js file and replace the line:
       var printer = status.drivers.escpos ? status.drivers.escpos.status : false);

       if( printer != 'connected' && printer != 'connecting'){
                   warning = true;
                   msg = msg ? msg + ' & ' : msg;
                   msg += _t('Fiscale');
               }
    with:
          var printer = status.drivers.escpos ? status.drivers.escpos.status : false;

          if( printer != 'connected' && printer != 'connecting'){
              warning = true;
              msg = msg ? msg + ' & ' : msg;
              msg += _t('Printer');
          }

          var printer = status.drivers.fiscalpos ? status.drivers.fiscalpos.status : false;

          if( printer != 'connected' && printer != 'connecting'){
              warning = true;
              msg = msg ? msg + ' & ' : msg;
              msg += _t('Fiscale');
          }         

* edit point_of_sale/static/src/js/screen.js as follows:
      // var receipt = QWeb.render('XmlReceipt',env);
      var receipt = this.pos.get_order().export_for_printing();
      this.pos.proxy.print_receipt(receipt,true);

* edit point_of_sale/static/src/js/device.js as follows:

 add fiscalPrinter as print_receipt function parameter:

       print_receipt: function(receipt,fiscalPrinter = false){

  replace the line `self.message('print_xml_receipt',{ receipt: r },{ timeout: 5000 })` with

      var methodName = fiscalPrinter ? 'print_fiscal_receipt' : 'print_xml_receipt'
      self.message(methodName,{ receipt: r },{ timeout: 5000 })
