# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# © 2015 Eezee-It, MONK Software, Vauxoo
# © 2013 Camptocamp
# © 2009-2013 Akretion,
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

{
    'name': 'Return Merchandise Authorization (RMA)',
    'version': '9.0.1.0.0',
    'license': 'LGPL-3',
    'category': 'RMA',
    'summary': 'Introduces the return merchandise authorization (RMA) process '
               'in odoo',
    'author': "Akretion, Camptocamp, Eezee-it, MONK Software, Vauxoo, Eficent,"
              "Praxya,"
              "Odoo Community Association (OCA)",
    'website': 'http://www.github.com/OCA/rma',
    'depends': ['account',
                'stock',
                'mail',
                'procurement'],
    'demo': ['demo/stock.xml',
             'demo/rma_operation.xml'],
    'data': [
            'security/rma.xml',
             'security/ir.model.access.csv',
             'data/rma_sequence.xml',
             'views/rma_order_view.xml',
             'views/rma_operation_view.xml',
             'views/rma_rule_view.xml',
             'views/rma_order_line_view.xml',
             'views/stock_view.xml',
             'views/stock_warehouse.xml',
             'views/invoice_view.xml',
             'views/product_view.xml',
             'views/procurement_view.xml',
             'views/res_company_view.xml',
             'views/rma_external_invoice_line.xml',
             'wizards/rma_make_picking.xml',
             'wizards/rma_add_invoice.xml',
             'wizards/rma_refund.xml',
             'wizards/stock_config_settings.xml'
             ],
    'installable': True,
    'auto_install': False,
    "post_init_hook": "post_init_hook",
}
