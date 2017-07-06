# -*- coding: utf-8 -*-
# © 2017 Praxya <drl.9319@gmail.com>
from openerp import models, api, fields, _
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from dateutil.relativedelta import relativedelta


class RmaOrderLine(models.Model):
    _inherit = 'rma.order.line'

    @api.one
    @api.depends('invoice_line_id')
    def _compute_warranty(self):
        """
            Overwrite this function becouse how it's possbile obtain a invoice
            from old system betwen rma.external.invoice.line model, this
            not is a invoice for them the field invoice_id field in
            rma.order.lines is empy but, with the field date its enough.
        """
        super(RmaOrderLine, self)._compute_warranty()
        if self.warranty_state == 'undefined':
            limit = False
            state = "undefined"
            line = self.invoice_line_id
            invoice_date = self.invoice_date
            if self.type == 'supplier':
                seller = self.product_id.seller_ids.filtered(
                    lambda p: p.name == self.invoice_partner_id)
                warranty = seller.warranty_duration or False
            else:
                warranty = line.product_id.warranty

            if warranty and invoice_date:
                limit = datetime.strptime(
                    invoice_date, DEFAULT_SERVER_DATE_FORMAT) + relativedelta(
                    months=int(warranty))
            if limit and warranty > 0:
                if limit < datetime.now():
                    state = 'expired'
                else:
                    state = 'valid'
            if limit:
                self.limit = datetime.strftime(
                    limit, DEFAULT_SERVER_DATE_FORMAT)
            self.warranty_state = state

    invoice_date = fields.Date(
        string='Invoice Date')

    invoice_partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Old invoice partner')

    warranty_state = fields.Selection(
        compute=_compute_warranty)
