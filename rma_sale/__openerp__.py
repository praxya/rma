# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'RMA Sale',
    'version': '9.0.1.0.0',
    'category': 'RMA',
    'summary': 'RMA from SO',
    'description': """
    RMA from SO
""",
    'author': 'Eficent',
    'website': 'http://www.github.com/OCA/rma',
    'depends': ['rma', 'sale'],
    'data': ['views/rma_view.xml'],
    'installable': True,
    'auto_install': False,
}
