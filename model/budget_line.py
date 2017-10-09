# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions, tools, _
from openerp.exceptions import Warning

import pprint
#Import logger
import logging
#Get the logger
_logger = logging.getLogger(__name__)

class BudgetLine(models.Model):

    _inherit = 'crossovered.budget.lines'

    def _default_budget(self):
        
        objs = self.env['crossovered.budget'].sudo().search([['date_from', '<=', fields.Date.today()], 
                                                                ['date_to', '>=', fields.Date.today()]], limit=1)
        if(objs):
            return objs[0]
        
        return False
    
    def _default_budget_post(self):
        
        objs = self.env['account.budget.post'].sudo().search([], limit=1)
        if(objs):
            return objs[0]
        
        return False
        
    # inherited
    crossovered_budget_id = fields.Many2one(default=_default_budget)
    general_budget_id = fields.Many2one(default=_default_budget_post)

    # added
    analytic_account_name = fields.Char(related='analytic_account_id.name')
    partner_id = fields.Many2one(related='analytic_account_id.partner_id')
    
    
