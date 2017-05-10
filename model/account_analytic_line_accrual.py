# -*- coding: utf-8 -*-
from openerp import models, fields, api

import logging
_logger = logging.getLogger(__name__)

class AccountAnalyticLineAccrual(models.Model):
    _name = 'account.analytic.line.accrual'

    line_id = fields.Many2one('account.analytic.line',required=True,auto_join=True,ondelete='cascade')

    line_date = fields.Date(string='Line date', related='line_id.date', readonly=True)
    line_account_id = fields.Many2one(related='line_id.account_id', readonly=True)
    line_ref = fields.Char(related='line_id.ref', readonly=True)
    line_invoice_id = fields.Many2one(related='line_id.invoice_id', readonly=True)
    line_amount = fields.Float(string='Line amount', related='line_id.amount', readonly=True)

    date = fields.Date(required=True)
    amount = fields.Float(required=True)

    @api.multi
    def write(self, vals):
        
        # try delete invalid rows
        if('line_id' in vals and not vals['line_id']):
            for r in self:
                r.unlink()
            
            return True
        
        return super(AccountAnalyticLineAccrual, self).write(vals)
            
        
    
            
    
