


{
    'name': 'Fiscal Pos Hardware Driver',
    'version': '1.0',
    'category': 'Hardware Drivers',
    'sequence': 6,
    'website': 'https://www.odoo.com/page/point-of-sale',
    'summary': 'Hardware Driver for Fiscal Printers and Cashdrawers',
    'description': """
ESC/POS Hardware Driver
=======================

This module allows openerp to print with ESC/POS compatible printers and
to open ESC/POS controlled cashdrawers in the point of sale and other modules
that would need such functionality.

""",
    'depends': ['hw_proxy'],
    'external_dependencies': {
        'python' : ['usb.core','serial','qrcode'],
    },
    'test': [
    ],
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
