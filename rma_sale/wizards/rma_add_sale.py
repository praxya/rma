# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# © 2015 Eezee-It, MONK Software, Vauxoo
# © 2013 Camptocamp
# © 2009-2013 Akretion,
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

import time
from openerp import models, fields, exceptions, api, _
from openerp.exceptions import ValidationError
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT_FORMAT
import openerp.addons.decimal_precision as dp


class RmaAddSale(models.TransientModel):
    _name = 'rma_add_sale'
    _description = 'Wizard to add rma lines'

    @api.model
    def default_get(self, fields):
        res = super(RmaAddSale, self).default_get(fields)
        rma_obj = self.env['rma.order']
        rma_id = self.env.context['active_ids'] or []
        active_model = self.env.context['active_model']
        if not rma_id:
            return res
        assert active_model == 'rma.order', 'Bad context propagation'

        rma = rma_obj.browse(rma_id)
        res['rma_id'] = rma.id
        res['partner_id'] = rma.partner_id.id
        res['sale_id'] = False
        res['sale_line_ids'] = False
        return res

    rma_id = fields.Many2one('rma.order',
                              string='RMA Order',
                              readonly=True,
                              ondelete='cascade')

    partner_id = fields.Many2one(comodel_name='res.partner', string='Partner',
                                 readonly=True)
    sale_id = fields.Many2one(comodel_name='sale.order', string='Order')
    sale_line_ids = fields.Many2many('sale.order.line',
                                     'rma_add_sale_add_line_rel',
                                     'sale_line_id', 'rma_add_sale_id',
                                     readonly=False,
                                     string='Sale Lines')


    def _prepare_rma_line_from_sale_order_line(self, line):
        operation = line.product_id.rma_operation_id and \
                    line.product_id.rma_operation_id.id or False
        if not operation:
            operation = line.product_id.categ_id.rma_operation_id and \
                        line.product_id.categ_id.rma_operation_id.id or False
        data = {
            'sale_line_id': line.id,
            'product_id': line.product_id.id,
            'name': line.name,
            'origin': line.order_id.name,
            'uom_id': line.product_uom.id,
            'operation_id': operation,
            'product_qty': line.product_uom_qty,
            'price_unit': line.currency_id.compute(
                line.price_unit, line.currency_id, round=False),
            'rma_id': self.rma_id.id
        }
        return data

    @api.model
    def _get_rma_data(self):
        data = {
            'date_rma': fields.Datetime.now(),
            'delivery_address_id': self.sale_id.partner_id.id,
            'invoice_address_id': self.sale_id.partner_id.id
        }
        return data

    @api.model
    def _get_existing_sale_lines(self):
        existing_sale_lines = []
        for rma_line in self.rma_id.rma_line_ids:
            existing_sale_lines.append(rma_line.sale_line_id)
        return existing_sale_lines

    @api.multi
    def add_lines(self):
        rma_line_obj = self.env['rma.order.line']
        existing_sale_lines = self._get_existing_sale_lines()
        for line in self.sale_line_ids:
            # Load a PO line only once
            if line not in existing_sale_lines:
                data = self._prepare_rma_line_from_sale_order_line(line)
                rma_line_obj.create(data)
        rma = self.rma_id
        data_rma = self._get_rma_data()
        rma.write(data_rma)
        return {'type': 'ir.actions.act_window_close'}
