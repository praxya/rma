# -*- coding: utf-8 -*-
# © 2017 Praxya <drl.9319@gmail.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
{
    'name': 'RMA Serial Number',
    'version': '8.0.1.0.0',
    'category': 'RMA',
    'summary': """
    RMA Serial Number

""",
    'author': 'Praxya',
    'website': 'http://www.github.com/OCA/rma',
    'depends': [
        'rma',
        'rma_warranty',
        'stock',
        'sale',
        'purchase',
        'account',
        'product',
    ],
    'data': [
        'wizards/rma_add_from_serial_number.xml',
        'views/rma_order_view.xml',
    ],
    'installable': True,
}
