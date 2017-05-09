# -*- coding: utf-8 -*-
from openerp import models, fields, api

import logging
_logger = logging.getLogger(__name__)

class AccountAnalyticLineAccrual(models.Model):
    _name = 'account.analytic.line.accrual'

    line_id = fields.Many2one('account.analytic.line', 'accrual_ids',required=True,auto_join=True)
    date = fields.Date(required=True)
    amount = fields.Float(required=True)
