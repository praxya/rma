# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models
from openerp.addons import decimal_precision as dp
from random import randint


class RmaOrder(models.Model):
    _inherit = "rma.order"

    @api.depends('rma_line_ids')
    @api.multi
    def _compute_po_line_count(self):
        for rec in self:
            return len(rec.rma_line_ids)

    add_purchase_id = fields.Many2one(comodel_name='purchase.order',
                                      string='Add Purchase Order',
                                      ondelete='set null')
    po_line_count = fields.Integer(compute=_compute_po_line_count,
                                   string='# of PO lines',
                                   copy=False, default=0)

    def _prepare_rma_line_from_po_line(self, rma_id, line):
        data = {
            'purchase_line_id': line.id,
            'product_id': line.product_id.id,
            'name': line.name,
            'origin': line.order_id.name,
            'uom_id': line.product_uom.id,
            'product_id': line.product_id.id,
            'qty_to_receive': line.product_qty,
            'qty_expected_to_refund': line.product_qty,
            'operation': 'refund',
            'price_unit': line.price_unit,
            # 'refund_status': 'no',
            # 'ship_status': 'no',
            'rma_id': rma_id
        }
        return data

    @api.onchange('add_purchase_id')
    def on_change_purchase(self):
        if not self.add_purchase_id:
            return {}
        if not self.partner_id:
            self.partner_id = self.add_purchase_id.partner_id.id

        new_lines = self.env['rma.order.line']
        invoices = self.env['account.invoice']
        for line in self.add_purchase_id.order_line:
            # Load a PO line only once
            if line in self.rma_line_ids.mapped('purchase_line_id'):
                continue
            data = self._prepare_rma_line_from_po_line(self.id, line)
            new_line = new_lines.new(data)
            new_lines += new_line

        self.rma_line_ids += new_lines
        self.add_purchase_id = False
        return {}

    @api.multi
    def action_view_po_lines(self):
        """
        This function returns an action that display existing vendor refund
        bills of given purchase order id.
        When only one found, show the vendor bill immediately.
        """
        action = self.env.ref('rma_purchase.action_purchase_line_rma_tree')
        result = action.read()[0]
        po_lines =[]
        for rec in self:
            for line in rec.rma_line_ids:
                if line.purchase_line_id:
                    po_lines.append(line.purchase_line_id.id)
            # override the context to get rid of the default filtering
            result['context'] = {'type': 'purchases',
                                 'default_rma_id': rec.id}

        # choose the view_mode accordingly
        if len(po_lines) != 1:
            result['domain'] = "[('id', 'in', " + \
                               str(po_lines) + ")]"
        elif len(po_lines) == 1:
            res = self.env.ref('purchase.purchase_order_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = po_lines
        return result


class RmaOrderLine(models.Model):
    _inherit = "rma.order.line"

    purchase_line_id = fields.Many2one('purchase.order.line',
                                       string='Purchase Line',
                                       ondelete='set null',
                                       index=True, readonly=True)
    purchase_id = fields.Many2one('purchase.order', string='Source',
                                  related='purchase_line_id.order_id',
                                  ondelete='set null', index=True,
                                  readonly=True)
