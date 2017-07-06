# -*- coding: utf-8 -*-
# © 2017 Praxya <drl.9319@gmail.com>
from openerp import models, api, fields, _
from openerp.exceptions import Warning as UserError


class RmaAddFromSerialNumber(models.TransientModel):
    _name = 'rma.add.from.serial.number'

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True)

    serial_number_id = fields.Many2one(
        comodel_name='stock.production.lot',
        string='Serial Number',
        domain="[('product_id', '=', product_id)]",
        required=True)

    rma_id = fields.Many2one(
        comodel_name='rma.order',
        string='RMA Order',
        readonly=True,
        ondelete='cascade')

    rma_type = fields.Selection(
        [('supplier', 'Supplier'),
         ('customer', 'Customer')],
        string='Rma Type')

    def _search_invoice_in_odoo(self):
        """
            This function search an invoice exist in Odoo in relation with
            the serial number through stock.move origin field.

            The stock.quant objet have relation with stock.move and The
            stock.move hace the field origin, and this field have purchase
            or invoice order, through this order can be view the related
            invoice.

            Returns:
                invoice_id: False if don't exist invoice, obj invoice if exist.
        """
        stock_quant_obj = self.env['stock.quant']
        stock_move_obj = self.env['stock.move']
        sale_obj = self.env['sale.order']
        purchase_obj = self.env['purchase.order']
        invoice_id = False
        stock_quant_ids = stock_quant_obj.search([
            ('lot_id', '=', self.serial_number_id.id)
        ])

        if len(stock_quant_ids) > 0:
            stock_move_ids = stock_move_obj.search([
                ('quant_ids', 'in', stock_quant_ids.ids)
            ])
            purchase_list = []
            sale_list = []
            for stock_move in stock_move_ids:
                # Search the purchase or sale order related
                if self.rma_type == "supplier":
                    if stock_move.origin:
                        purchase_id = purchase_obj.search([
                            ('name', '=', stock_move.origin)
                        ])
                        if len(purchase_id) == 1:
                            purchase_list.append(purchase_id)
                elif self.rma_type == "customer":
                    if stock_move.origin:
                        sale_id = sale_obj.search([
                            ('name', '=', stock_move.origin)
                        ])
                        if len(sale_obj) == 1:
                            sale_list.append(sale_id)

            # Search the related invoices from purchase and sale
            for purchase in purchase_list:
                if len(purchase.invoice_ids) > 0:
                    invoice_id = purchase.invoice_ids[0]
            for sale in sale_list:
                # TODO its posible Odoo hace several invoices from the same
                # sale, ask where invoice must cath last or firts...
                if len(sale.invoice_ids) > 0:
                    invoice_id = sale.invoice_ids[0]
        return invoice_id

    def _search_external_invoice(self):
        """
            This function search product and serial number in invoices
            from old system lines.

            Returns:
                bool: False if not exist,
                    obj: rma.external.invoice.line object.
        """
        external_invoice_obj = self.env['rma.external.invoice.line']
        external_invoice_id = False
        external_invoice_ids = external_invoice_obj.search([
            ('product_id', '=', self.product_id.id),
            ('serial_number', '=', self.serial_number_id.name)
        ])
        if len(external_invoice_ids) == 1:
            external_invoice_id = external_invoice_ids[0]

        return external_invoice_id

    def _prepare_rma_line(self, invoice_id=False, external_invoice_id=False):
        """
            This function prepare a dictionary with the values to make
            a new rma_line_ids

            Args:
                invoice_id (obj): account.invoice
                external_invoice_id (obj): rma.external.invoice.line

            Returns:
                dictionary:  with the values to make a new rma_line_ids.
        """
        operation = self.product_id.rma_operation_id or False
        if not operation:
            operation = self.product_id.categ_id.rma_operation_id or False
        data = {
            # 'invoice_line_id': line.id,
            'product_id': self.product_id.id,
            'name': self.product_id.name_template,
            'rma_id': self.rma_id.id,
            'product_qty': 1,
        }
        if invoice_id:
            data.update({
                'origin': invoice_id.number,
                # 'uom_id': line.uos_id.id,
                # 'price_unit': invoice_id.currency_id.compute(
                #     line.price_unit, invoice_id.currency_id, round=False),
                'delivery_address_id': invoice_id.partner_id.id,
                'invoice_address_id': invoice_id.partner_id.id,
                'invoice_date': invoice_id.date_invoice,
                'invoice_partner_id': invoice_id.partner_id.id,
            })
        elif external_invoice_id:
            data.update({
                'origin': external_invoice_id.invoice_number,
                # 'uom_id': line.uos_id.id,
                # 'price_unit': invoice_id.currency_id.compute(
                #     line.price_unit, invoice_id.currency_id, round=False),
                'delivery_address_id': external_invoice_id.partner_id.id,
                'invoice_address_id': external_invoice_id.partner_id.id,
                'invoice_date': external_invoice_id.invoice_date,
                'invoice_partner_id': external_invoice_id.partner_id.id,
            })
        if operation:
            data.update({
                'operation_id': operation.id,
            })
        if not operation:
            operation = self.env['rma.operation'].search(
                [('type', '=', self.rma_id.type)], limit=1)
            if not operation:
                raise UserError(_("Please define an operation first"))
        if not operation.in_route_id or not operation.out_route_id:
            route = self.env['stock.location.route'].search(
                [('rma_selectable', '=', True)], limit=1)
            if not route:
                raise UserError(_("Please define an rma route"))
        data.update(
            {'in_route_id': operation.in_route_id.id or route.id,
             'out_route_id': operation.out_route_id.id or route.id,
             'receipt_policy': operation.receipt_policy,
             'location_id':
                operation.location_id.id or
                self.env.ref('stock.stock_location_stock').id,
             'operation_id': operation.id,
             'refund_policy': operation.refund_policy,
             'delivery_policy': operation.delivery_policy
             })
        return data

    @api.model
    def _get_rma_data(self, invoice_id=False, external_invoice_id=False):
        if invoice_id:
            data = {
                'date_rma': fields.Datetime.now(),
                'delivery_address_id': invoice_id.partner_id.id,
                'invoice_address_id': invoice_id.partner_id.id
            }
        elif external_invoice_id:
            data = {
                'date_rma': fields.Datetime.now(),
                'delivery_address_id': external_invoice_id.partner_id.id,
                'invoice_address_id': external_invoice_id.partner_id.id
            }
        return data

    @api.multi
    def search_invoice_serial_number(self):
        """
            This function is call from confirm button in
            rma_add_from_serial_number

            Args:
                param (type): des_example

            Returns:
                bool: True if successful, False otherwise.
        """
        rma_line_obj = self.env['rma.order.line']
        external_invoice_id = False
        # Search the invoice in Odoo system
        invoice_id = self._search_invoice_in_odoo()
        if not invoice_id:
            # If no exist invoice must search the serial number in old invoices
            # from the old system
            external_invoice_id = self._search_external_invoice()
        if not external_invoice_id and not invoice_id:
            raise UserError(_(
                    "This serial number haven't Odoo invoice related and "
                    "haven't invoice from the old system"))
        # Prepare and create the new rma line
        ram_line_data = self._prepare_rma_line(
            invoice_id=invoice_id, external_invoice_id=external_invoice_id)
        rma_line_obj.create(ram_line_data)

        rma_data = self._get_rma_data(
            invoice_id=invoice_id, external_invoice_id=external_invoice_id)
        self.rma_id.write(rma_data)
        return {'type': 'ir.actions.act_window_close'}
