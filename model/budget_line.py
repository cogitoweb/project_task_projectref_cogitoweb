# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions, tools

import pprint
#Import logger
import logging
#Get the logger
_logger = logging.getLogger(__name__)

class BudgetLine(models.Model):

    _inherit = 'crossovered.budget.lines'

    sale_order_id = fields.Many2one('sale.order', string="Sale Order")

    invoice_date = fields.Date()

    def _get_start_date(self):
        if(self.analytic_account_id):
            return self.analytic_account_id.date_start

    def _get_end_date(self):
        if(self.analytic_account_id):
            return self.analytic_account_id.date

    def _get_analytic_account(self):
        if(self.sale_order_id):
            return self.sale_order_id.analytic_account_id

    defaults = {
        'date_from': _get_start_date,
        'date_to': _get_end_date,
        'analytic_account_id': _get_analytic_account
    }


