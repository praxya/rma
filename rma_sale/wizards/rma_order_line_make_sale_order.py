# -*- coding: utf-8 -*-
# Copyright 2016 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).

import openerp.addons.decimal_precision as dp
from openerp import _, api, exceptions, fields, models


class RmaLineMakeSaleOrder(models.TransientModel):
    _name = "rma.order.line.make.sale.order"
    _description = "RMA Line Make Sales Order"

    partner_id = fields.Many2one('res.partner', string='Customer',
                                 required=False,
                                 domain=[('supplier', '=', True)])
    item_ids = fields.One2many(
        'rma.order.line.make.sale.order.item',
        'wiz_id', string='Items')
    sale_order_id = fields.Many2one('sale.order',
                                    string='Sales Order',
                                    required=False,
                                    domain=[('state', '=', 'draft')])

    @api.model
    def _prepare_item(self, line):
        return {
            'line_id': line.id,
            'rma_line_id': line.id,
            'product_id': line.product_id.id,
            'name': line.name or line.product_id.name,
            'product_qty': line.qty_to_sell,
            'product_uom_id': line.uom_id.id,
        }

    @api.model
    def default_get(self, fields):
        res = super(RmaLineMakeSaleOrder, self).default_get(
            fields)
        rma_line_obj = self.env['rma.order.line']
        rma_line_ids = self.env.context['active_ids'] or []
        active_model = self.env.context['active_model']

        if not rma_line_ids:
            return res
        assert active_model == 'rma.order.line', \
            'Bad context propagation'

        items = []
        lines = rma_line_obj.browse(rma_line_ids)
        for line in lines:
            items.append([0, 0, self._prepare_item(line)])
        customers = lines.mapped('partner_id')
        if len(customers) == 1:
            res['partner_id'] = customers.id
        res['item_ids'] = items
        return res

    @api.model
    def _prepare_sale_order(self, warehouse, company):
        if not self.partner_id:
            raise exceptions.Warning(
                _('Enter a customer.'))
        customer = self.partner_id
        data = {
            'origin': '',
            'partner_id': customer.id,
            'warehouse_id': warehouse.id,
            'company_id': company.id,
            }
        return data

    @api.model
    def _prepare_sale_order_line(self, so, item):
        product = item.product_id
        vals = {
            'name': product.name,
            'order_id': so.id,
            'product_id': product.id,
            'product_uom': product.uom_po_id.id,
            'route_id': item.line_id.operation_id.route_customer.id,
            'product_qty': item.product_qty,
            'rma_line_id': item.line_id.id
        }
        if item.free_of_charge:
            vals['price_unit'] = 0.0
        return vals

    @api.multi
    def make_sale_order(self):
        res = []
        sale_obj = self.env['sale.order']
        so_line_obj = self.env['sale.order.line']
        sale = False

        for item in self.item_ids:
            line = item.line_id
            if item.product_qty <= 0.0:
                raise exceptions.Warning(
                    _('Enter a positive quantity.'))

            if self.sale_order_id:
                sale = self.sale_order_id
            if not sale:
                po_data = self._prepare_sale_order(
                    line.rma_id.warehouse_id, line.company_id)
                sale = sale_obj.create(po_data)

            so_line_data = self._prepare_sale_order_line(sale, item)
            so_line_obj.create(so_line_data)
            res.append(sale.id)

        return {
            'domain': "[('id','in', ["+','.join(map(str, res))+"])]",
            'name': _('Quotations'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'view_id': False,
            'context': False,
            'type': 'ir.actions.act_window'
        }


class RmaLineMakeSaleOrderItem(models.TransientModel):
    _name = "rma.order.line.make.sale.order.item"
    _description = "RMA Line Make Sale Order Item"

    wiz_id = fields.Many2one(
        'rma.order.line.make.sale.order',
        string='Wizard', required=True, ondelete='cascade',
        readonly=True)
    line_id = fields.Many2one('rma.order.line',
                              string='RMA Line',
                              required=True)
    rma_id = fields.Many2one('rma.order', related='line_id.rma_id',
                             string='RMA Order', readonly=True)
    product_id = fields.Many2one('product.product', string='Product')
    name = fields.Char(string='Description', required=True)
    product_qty = fields.Float(string='Quantity to sell',
                               digits=dp.get_precision('Product UoS'))
    product_uom_id = fields.Many2one('product.uom', string='UoM',
                                     readonly=True)
    free_of_charge = fields.Boolean('Free of Charge')
