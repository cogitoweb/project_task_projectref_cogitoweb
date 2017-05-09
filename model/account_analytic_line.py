from openerp import fields, models, api

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'
    
    accrual_ids = fields.One2many('account.analytic.line.accrual', 'line_id')