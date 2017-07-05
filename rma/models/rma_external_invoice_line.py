# -*- coding: utf-8 -*-
# © 2017 Praxya <drl.9319@gmail.com>
from openerp import models, api, fields, _


class RmaExternalInvoiceLine(models.Model):
    _name = 'rma.external.invoice.line'
    '''
        This model allow register invoices, products and serial numbers
        from the other system to use this data in Odoo rma.
        Note: To can use the serial numbers you must insert previus this
        serial numbers in Odoo.
    '''

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Client/customer')

    invoice_number = fields.Char(
        string='Invoice Number',
        help="In this field you must insert the invoice number from you old"
        "system")

    invoice_date = fields.Date(
        string='Invoice Date')

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product')

    serial_number = fields.Char(
        string='Serial number')
