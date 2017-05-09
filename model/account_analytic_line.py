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

        _logger.info(pprint.pformat(vals))
    
        if('amount' not in vals and 'account_id' not in vals and 'journal_id' not in vals and 'date' not in vals and 'invoice_id' not in vals and 'unit_amount' not in vals and 'general_account_id' not in vals):
            return True
        else:
            for r in self:
                if r.invoice_id:
                    raise ValidationError(_('You cannot modify an invoiced analytic line!'))
        
        return True
