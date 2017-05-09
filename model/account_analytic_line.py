from openerp import fields, models, api

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'
    
    accrual_ids = fields.One2many('account.analytic.line.accrual', 'line_id')
    
    @api.model
    def _check_inv(self, vals):
    
        if(not vals.has_key('amount') and not vals.has_key('account_id') and not vals.has_key('journal_id') and not vals.has_key('date') and not vals.has_key('invoice_id') and not vals.has_key('unit_amount') and not vals.has_key('general_account_id')):
            return True

        return super(AccountAnalyticLine,self)._check_inv(vals)