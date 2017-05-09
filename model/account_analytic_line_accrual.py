# -*- coding: utf-8 -*-
from openerp import models, fields, api

import logging
_logger = logging.getLogger(__name__)

class AccountAnalyticLineAccrual(models.Model):
    _name = 'account.analytic.line.accrual'

    line_id = fields.Many2one('account.analytic.line',required=True,auto_join=True)

    line_date = fields.Date(string='Line date', related='line_id.date')
    line_account_id = fields.Many2one(related='line_id.account_id')
    line_ref = fields.Char(related='line_id.ref')
    line_invoice_id = fields.Many2one(related='line_id.invoice_id')
    line_amount = fields.Float(string='Line amount', related='line_id.amount')

    date = fields.Date(required=True)
    amount = fields.Float(required=True)
