from openerp import fields, models, api, _
from openerp.exceptions import ValidationError
import pprint

import logging
_logger = logging.getLogger(__name__)

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'
    
    accrual_ids = fields.One2many('account.analytic.line.accrual', 'line_id')
    
    @api.multi
    def _check_inv(self, vals):
        if('amount' not in vals and 'account_id' not in vals and 'journal_id' not in vals and 'date' not in vals and 'invoice_id' not in vals and 'unit_amount' not in vals and 'general_account_id' not in vals):
            return True
        else:
            for r in self:
                if r.invoice_id:
                    raise ValidationError(_('You cannot modify an invoiced analytic line!'))
        
        return True

    @api.multi
    def generate_accrual(self):

        active_ids = self._context.get('active_ids', [])
        records = self.env['account.analytic.line'].browse(active_ids)
    
        for r in records:
 
            if(r.invoice_id and r.journal_id and r.journal_id.type == 'sale' and not len(r.accrual_ids)):
                
                self.env['account.analytic.line.accrual'].sudo().create({
                    'line_id': r.id,
                    'date': r.date,
                    'amount': r.amount
                })
    
    
