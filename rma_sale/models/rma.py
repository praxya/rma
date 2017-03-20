# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models
from openerp.addons import decimal_precision as dp
from random import randint


class RmaOrder(models.Model):
    _inherit = "rma.order"

    add_sale_id = fields.Many2one(comodel_name='sale.order', string='Add Sale Order', ondelete='set null')
    @api.depends('rma_line_ids')
    @api.multi
    def _compute_so_line_count(self):
        for rec in self:
            return len(rec.rma_line_ids)

    so_line_count = fields.Integer(compute=_compute_so_line_count,
                                   string='# of SO lines',
                                   copy=False, default=0)

    def _prepare_rma_line_from_so_line(self, line):
        data = {
            'invoice_line_id': line.id,
            'product_id': line.product_id.id,
            'name': line.name,
            'origin': line.origin,
            'uom_id': line.uom_id.id,
            'product_id': line.product_id.id,
            'qty_expected': line.quantity,
            'qty_expected_to_refund': line.quantity,
            'price_unit': line.invoice_id.currency_id.compute(line.price_unit, line.currency_id, round=False),
            # 'refund_status': 'no',
            # 'ship_status': 'no'
        }
        return data

    @api.onchange('add_sale_id')
    def on_change_sale(self):
        if not self.add_sale_id:
            return {}
        if not self.partner_id:
            self.partner_id = self.add_sale_id.partner_id.id

        new_lines = self.env['rma.order.line']
        invoices = self.env['account.invoice']
        for line in self.add_sale_id.order_line:
            invoices |= line.invoice_lines.mapped('invoice_id')

        for invoice in invoices:
            for line in invoice.invoice_line_ids:
                # Load a PO line only once
                if line in self.rma_line_ids.mapped('invoice_line_id'):
                    continue
                data = self._prepare_rma_line_from_inv_line(line)
                new_line = new_lines.new(data)
                new_lines += new_line

        self.rma_line_ids += new_lines
        self.add_sale_id = False
        return {}



class RmaOrderLine(models.Model):
    _inherit = "rma.order.line"

    sale_line_id = fields.Many2one('sale.order.line', string='Sale Order Line', ondelete='set null',
                                       index=True, readonly=True)
    sale_id = fields.Many2one('sale.order', string='Source', related='sale_line_id.order_id',
                                  ondelete='set null', index=True, readonly=True)
