# hw_fiscalpos

#### Description


The odoo module is a modified version of hw_escpos to support the following fiscal printer:
   * FP-81, FP-81 S, FP-90 II ed FP-H6000 – firmware >= 4.008
   * FP-81 II, FP-81 II S, FP-81 II T ed FP-90 III – firmware >= 3.008


#### Installation

###### Requirements:
  * posbox
  * odoo server

###### What to do on posbox
* unzip/copy hw_fiscalpos dir into /home/pi/odoo/addons directory
* change the fs on posbox as writable `sudo mount -o remount,rw /root_bypass_ramdisks`
* edit /root_bypass_ramdisks/etc/init.d/odoo andreplace hw_escopos with hw_fiscalpos

###### What to do on point_of_sale addons
* edit point_of_sale/static/src/js/chrome.js file and replace all `escpos` with `fiscalpos`
* edit point_of_sale/static/src/js/screen.js as follows:
      // var receipt = QWeb.render('XmlReceipt',env);
      var receipt = this.pos.get_order().export_for_printing();
* edit point_of_sale/static/src/js/device.js as follows:
      //self.message('print_xml_receipt',{ receipt: r },{ timeout: 5000 })
      self.message('print_receipt',{ receipt: r },{ timeout: 5000 })
