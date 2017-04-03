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


class RmaMakePicking(models.TransientModel):
    _name = 'rma_make_picking.wizard'
    _description = 'Wizard to create pickings from rma lines'

    @api.model
    def _default_dest_location_id(self):
        if self.env.context.get('picking_type') == 'incoming':
            if self.warehouse_id:
                return self.warehouse_id.lot_rma_id.id
            if 'active_ids' in self.env.context:
                domain = [('id', 'in', self.env.context['active_ids'])]
                lines = self.env['rma.order.line']. \
                    search(domain, limit=1)
                return lines.rma_id.warehouse_id.lot_rma_id.id
        else:
            domain = [('id', 'in', self.env.context['active_ids'])]
            lines = self.env['rma.order.line']. \
                search(domain, limit=1)
            if lines.type == 'customer':
                return lines.rma_id.partner_id.property_stock_customer.id
            else:
                return lines.rma_id.partner_id.property_stock_supplier.id

    @api.model
    def _default_src_location_id(self):
        if self.env.context.get('picking_type') == 'outgoing':
            if self.warehouse_id:
                return self.warehouse_id.lot_rma_id.id
            if 'active_ids' in self.env.context:
                domain = [('id', 'in', self.env.context['active_ids'])]
                lines = self.env['rma.order.line']. \
                    search(domain, limit=1)
                return lines.rma_id.warehouse_id.lot_rma_id.id
        else:
            domain = [('id', 'in', self.env.context['active_ids'])]
            lines = self.env['rma.order.line']. \
                search(domain, limit=1)
            if lines.type == 'supplier':
                return lines.rma_id.partner_id.property_stock_supplier.id
            else:
                return lines.rma_id.partner_id.property_stock_customer.id

    @api.model
    def _default_rma_warehouse(self):
        domain = [('id', 'in', self.env.context['active_ids'])]
        lines = self.env['rma.order.line']. \
            search(domain, limit=1)
        return lines.rma_id.warehouse_id.id

    @api.returns('rma.order.line')
    def _prepare_item(self, line):
        values = {'product_id': line.product_id.id,
                  'name': line.name,
                  'product_qty': line.product_qty,
                  'uom_id': line.uom_id.id,
                  'qty_to_receive': line.qty_to_receive,
                  'qty_to_deliver': line.qty_to_deliver,
                  'line_id': line.id,
                  'wiz_id': self.env.context['active_id']}
        return values

    @api.model
    def default_get(self, fields):
        """Default values for wizard, if there is more than one supplier on
        lines the supplier field is empty otherwise is the unique line
        supplier.
        """
        res = super(RmaMakePicking, self).default_get(fields)
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
        res['item_ids'] = items
        return res

    warehouse_id = fields.Many2one(
        'stock.warehouse', string='Source Warehouse',
        default=_default_rma_warehouse,
        required=True,
        help="Warehouse where to take the replacement products for customers.",
    )

    src_location_id = fields.Many2one(
        'stock.location', string='Source Location',
        required=True,
        default=_default_src_location_id,
        help="Location where the returned products are from.")

    dest_location_id = fields.Many2one(
        'stock.location', string='Destination Location',
        required=True,
        default=_default_dest_location_id,
        help="Location where the returned products are from.")
    item_ids = fields.One2many(
        'rma_make_picking.wizard.item',
        'wiz_id', string='Items')

    def _get_procurement_group_data(self, rma):
        group_data = {
            'name': rma.name,
            'rma_id': rma.id,
        }
        return group_data

    @api.model
    def _get_suitable_route(self, rma_line, picking_type):
        """Return the routes to assign on RMA lines
        based on a location usage.

        If no match return None.
        """
        if rma_line.route_id:
            return rma_line.route_id
        else:
            routes = self.env['stock.location.route'].search(
                [('rma_selectable', '=', True),
                 ('warehouse_selectable', '=',True)])
            for route in routes:
                for rule in route.pull_ids:
                    if rule.picking_type_id.code == picking_type:
                        return route
        raise ValidationError(
            _('No route defined'))

    @api.model
    def _get_procurement_data(self, line, qty, route):
        procurement_data = {
            'name': line.product_id.name_template,
            'group_id': group.id,
            'origin': rma.rma_id.name,
            'warehouse_id': self.warehouse_id.id,
            'date_planned': time.strftime(DT_FORMAT),
            'product_id': line.product_id.id,
            'product_qty': qty,
            'product_uom': line.product_id.product_tmpl_id.uom_id.id,
            'location_id': self.dest_location_id.id,
            'company_id': line.company_id.id,
            'rma_line_id': line.id,
            'route_ids': [(6,0,route)]
        }
        return procurement_data

    @api.model
    def _create_procurement(self, rma_line, picking_type):
        procurement_group = self._get_procurement_group_data(rma_line)
        if picking_type == 'incoming':
            qty = rma_line.qty_to_receive
        else:
            qty = line.qty_to_deliver
        route = self._get_suitable_route(rma_line, picking_type)
        procurement_data = self._get_procurement_data(
            rma_line, procurement_group, qty, route)
        # create picking
        procurement = self.env['procurement.order'].create(procurement_data)
        procurement.run()
        action = procurement.do_view_pickings()
        return action


    @api.multi
    def action_create_picking(self):
        """Method called when the user clicks on create picking"""
        rma_line_ids = self.env['rma.order.line'].browse(
            self.env.context['active_ids'])
        picking_type = self.env.context.get('picking_type')
        for line in rma_line_ids:
            if line.state != 'approved':
                raise exceptions.Warning(
                    _('RMA %s is not approved') %
                    line.rma_id.name)
            if line.operation_id.type not in ('replace', 'repair') and \
                    picking_type == 'outgoing' and line.type == 'customer':
                raise exceptions.Warning(
                    _('Only refunds allowed for at least one line'))
            if line.operation_id.type not in ('replace', 'repair') and \
                    picking_type == 'incoming' and line.type == 'supplier':
                raise exceptions.Warning(
                    _('Only refunds allowed for at least one line'))
            return self._create_procurement(line, picking_type)

    @api.multi
    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}


class RmaMakePickingItem(models.TransientModel):
    _name = "rma_make_picking.wizard.item"
    _description = "Items to receive"

    wiz_id = fields.Many2one(
        'rma_make_picking.wizard',
        string='Wizard', required=True)
    line_id = fields.Many2one('rma.order.line',
                              string='RMA order Line',
                              required=True,
                              readonly=True)
    rma_id = fields.Many2one('rma.order',
                             related='line_id.rma_id',
                             string='RMA',
                             readonly=True)
    product_id = fields.Many2one('product.product', string='Product',
                                 readonly=True)
    name = fields.Char(string='Description', required=True)
    product_qty = fields.Float(
        string='Quantity Ordered', copy=False,
        digits=dp.get_precision('Product Unit of Measure'),
        readonly=True)
    qty_to_receive = fields.Float(
        string='Quantity To Receive',
        digits=dp.get_precision('Product Unit of Measure'))
    qty_to_deliver = fields.Float(
        string='Quantity To Deliver',
        digits=dp.get_precision('Product Unit of Measure'))
    uom_id = fields.Many2one('product.uom', string='Unit of Measure',
                             readonly=True)
