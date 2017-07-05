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
