# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'RMA Purchase',
    'version': '9.0.1.0.0',
    'category': 'RMA',
    'summary': 'RMA from PO',
    'description': """
    RMA from PO
""",
    'author': 'Eficent',
    'website': 'http://www.github.com/OCA/rma',
    'depends': ['rma', 'purchase'],
    'data': ['views/rma_view.xml'],
    'installable': True,
    'auto_install': False,
}
