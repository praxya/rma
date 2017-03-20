# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openerp import api, fields, models


class SaleOrder(models.Model):

    _inherit = "sale.order"

    rma_line_ids = fields.One2many(
        comodel_name='rma.order.line', inverse_name='sale_line_id',
        string="RMA", readonly=True,
        help="This will contain the rmas for the sale line")