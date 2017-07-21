# -*- coding: utf-8 -*-


from exceptions import *

def utfstr(stuff):
    """ converts stuff to string and does without failing if stuff is a utf8 string """
    if isinstance(stuff,basestring):
        return stuff
    else:
        return str(stuff)

class Fiscalpos:
    """ FiscalPos Printer object """
    device    = None

    def printQRCode(self,text,operator=1):
        self._sendMsg('1', '075', str(operator).zfill(2)+'001'+'00'+'008'+'!9'+'2'+'00'+'92'+text.ljust(256))

    def beginFiscalReceipt(self,operator=1):
        self._sendMsg('1', '085', str(operator).zfill(2))

    def endFiscalReceipt(self, operator=1):
        self._sendMsg('1', '087', str(operator).zfill(2))

    def beginNoFiscalReceipt(self, operator=1):
        self._sendMsg('1', '063', str(operator).zfill(2))
        # self.__extract_status

    def printNoFiscalData(self,data,operator=1):
        self._sendMsg('1', '064', str(operator).zfill(2) +'2'+data.ljust(46))


    def endNoFiscalReceipt(self, operator=1):
        self._sendMsg('1', '065', str(operator).zfill(2))

    def beginFiscalDocument(self, operator=1):
        '''
        Method which starts fiscal receipt transaction
        :param operator: numeric value to identify the operator
        :return: 
        '''
        self._sendMsg('1', '095', str(operator).zfill(2))

    def endFiscalDocument(self, operator=1):
        '''
        Method which close a fiscal document transaction
        :param operator: 
        :return: 
        '''
        self._sendMsg('1', '097', str(operator).zfill(2))

    def printFiscalDocumentAmount(self,operator=1):
        
         
        self._sendMsg('1', '096', str(operator).zfill(2) + '0000')

    def displayAdvertismentText(self,text,operator=1):
        self._sendMsg('1','062',str(operator).zfill(2)+'0'+text.ljust(40)+'00')

    def feed(self,operator=1):
        self._sendMsg('1', '148', str(operator).zfill(2)+'1')

    def printRecItem(self,descriptionItem,quantity,unitPrice,rep=1,operator=1):
        self._sendMsg('1', '080', str(operator).zfill(2) + descriptionItem.ljust(38) + str(quantity).zfill(7) + str(unitPrice).zfill(9) + str(rep).zfill(2) + '1')

    def printRecReturnItem(self, description, quantity, unitPrice, rep=1, operator=1):
        self._sendMsg('1', '081', str(operator).zfill(2) + description.ljust(38) + str(quantity).zfill(7) + str(unitPrice).zfill(
            9) + str(rep).zfill(2) + '1')

    def printRecCancelItem(self, description, quantity, unitPrice, rep=1, operator=1):
        self._sendMsg('1', '082', str(operator).zfill(2) + description.ljust(38) + str(quantity).zfill(7) + str(unitPrice).zfill(
            9) + str(rep).zfill(2) + '1')

    def printRecDiscountItem(self, description, amount, rep=1, operator=1):
        self._sendMsg('1', '083', str(operator).zfill(2) + description.ljust(38) + str(amount).zfill(
            9) + '0'+ str(rep).zfill(2) + '1')

    def printRecDiscountPercentItem(self,value,operator=1):
        '''
        Apply a discount in percent
        :param operator:
        :return:
        '''
        self._sendMsg('1', '023', str(operator).zfill(2)+str(value).zfill(4))

    def printRecIncreaseItem(self, description, amount, rep=1, operator=1):
        self._sendMsg('1', '083', str(operator).zfill(2) + description.ljust(38) + str(amount).zfill(
            9) + '5'+ str(rep).zfill(2) + '1')

    def printRecTicketPayment(self,value,ticketTypeNumber=1,operator=1):
        self._sendMsg('1', '046', str(operator).zfill(2)+str(ticketTypeNumber).zfill(2)+str(value).zfill(2))

    def reprintLastFiscalReceiptOrCreditNote(self,operator=1):
        self._sendMsg('1','047',str(operator).zfill(2))

    def printRecPayment(self,description,amount,operator=1,paymentType=0,index=0):
        '''
         This method  must be used before to end the 'endFiscalReceipt'
        :param description: ex: Contanti
        :param amount: total amount with tax
        :param operator:
        :param paymentType:
                0 = Cash
                1 = Check
                2 = Credit Card
                3 = Ticket
        :param index: it depends on payment type :
                        Cash : 00
                        Cash with description: 01-05
                        Credit card or Ticket> 01-10 according to the number of the ticket type assigned by means of


        :return:
        '''
        self._sendMsg('1', '084', str(operator).zfill(2) + description.ljust(38) + str(amount).zfill(9) + str(paymentType).zfill(1) + str(index).zfill(2) + '1')

    def printRecSubtotal(self,operator=1):
        self._sendMsg('1', '086', str(operator).zfill(2) +'1'+'00')

    def displayRecSubtotal(self,operator=1):
        self._sendMsg('1', '086', str(operator).zfill(2) + '2' + '00')

    #Annulla completamente lo scontrino fiscale, nota di credito o fattura diretta
    def printRecVoid(self, operator=1):
        self._sendMsg('1', '028', str(operator).zfill(2))

    def printAddedLine(self,text46,rowNumber,operator=1):
        '''
        add line after total
        :param text: 40 180dpi o 46 203 dpi
        :param rowNumber:
        :param operator:
        :return:
        '''
        self._sendMsg('1', '078', str(operator).zfill(2)+'2'+str(rowNumber).zfill(2)+'1'+'1'+text46.ljust(46))

    def printAddedHeader(self,text46,rowNumber,operator=1):
        '''
        add line after company's information header before begin operations
        :param text: 40 180dpi o 46 203 dpi
        :param rowNumber: 0-9
        :param operator:
        :return:
        '''
        self._sendMsg('1', '078', str(operator).zfill(2)+'1'+str(rowNumber).zfill(2)+'1'+'1'+text46.ljust(46))

    def printAddedDescription(self,text,rowNumber,operator=1):
        self._sendMsg('1', '078', str(operator).zfill(2)+'4'+str(rowNumber).zfill(2)+'1'+'1'+text.ljust(46))

    # Permette di annullare l’ultima operazione di vendita, storno, reso, sconto o maggiorazione. Non è utilizzabile durante la fase di pagamento
    def printRecVoidItem(self, operator=1):
        self._sendMsg('1', '027', str(operator).zfill(2))

    def printDailyReport(self,operator=1):
        self._sendMsg('2', '001', str(operator).zfill(2))

    def reset(self,operator=1):
        '''Comanda il reset della stampante che in seguito:
            Pone la stampante in stato registrazione indipendentemente dallo stato corrente.
            Chiude eventuali scontrini non-fiscali aperti.
            Annulla eventuali scontrini fiscali aperti.
            Annulla eventuali note di credito aperte.
            Annulla eventuali fatture dirette aperte stampando due copie.
            Annulla eventuali fatture libere aperte stampando una copia.
            Annulla un eventuale titolo d’accesso aperto ed inoltre fa tornare la stampante in modalità “SCONTRINO FISCALE”.
            Sblocca la tastiera precedentemente bloccata tramite comando 1-055.
            Pulisce il buffer della tastiera.
        '''
        self._sendMsg('1', '088', str(operator).zfill(2))

    def cashdraw(self, pin,operator=1):
        """ Send pulse to kick the cash drawer """
        if pin == 2:
            self._sendMsg('1', '050', str(operator).zfill(2)+'1'+'125'+'250')
        elif pin == 5:
            self._sendMsg('1', '050', str(operator).zfill(2)+ '2'+ '125'+ '250')
        else:
            raise CashDrawerError()

