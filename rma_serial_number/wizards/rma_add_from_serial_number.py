# -*- coding: utf-8 -*-
from openerp import models, api, fields, _


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

            Args:
                param (type): des_example

            Returns:
                invoice_id: False if don't exist invoice, obj invoice if exist.
        """
        stock_quant_obj = self.env['stock.quant']
        stock_move_obj = self.env['stock.move']
        sale_obj = self.env['sale.order']
        purchase_obj = self.env['purchase.order']
        invoice_id = False
        stock_quant_ids = stock_quant_obj.search([
            ('lot_id', 'in', self.serial_number_id.id)
        ])

        if len(stock_quant_ids) > 0:
            stock_move_ids = stock_move_obj.search([
                ('quant_ids', 'in', stock_quant_ids.ids)
            ])
            purchase_list = []
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
                    print "TODO search sale order"

            # Search the related invoices from purchase and sale
            for purchase in purchase_list:
                if len(purchase.invoice_ids) > 0:
                    invoice_id = purchase.invoice_ids[0]
        return invoice_id

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
        # Search the invoice in Odoo system
        invoice_id = self._search_invoice_in_odoo()
        if not invoice_id:
            # If no exist invoice must search the serial number in old invoices
            # from the old system
            print "TODO"
