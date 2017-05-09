from openerp import fields, models, api

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'
    
    accrual_ids = fields.One2many('account.analytic.line.accrual', 'line_id')
    
    @api.model
    def _check_inv(self, vals):
    
        if('amount' not in vals and 'account_id' not in vals and 'journal_id' not in vals and 'date' not in vals and 'invoice_id' not in vals and 'unit_amount' not in vals and 'general_account_id' not in vals):
            return True

        return super(AccountAnalyticLine,self)._check_inv(vals)