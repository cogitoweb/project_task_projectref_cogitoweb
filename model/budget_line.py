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
    sale_order_id = fields.Many2one('sale.order', string="Sale Order")
    sale_order_state = fields.Selection(related='sale_order_id.state')
    invoiced = fields.Boolean(defaut=False)
    invoice_date = fields.Date()
    
    @api.onchange('invoice_date')
    def onchange_invoice_date(self):
        self.paid_date = self.invoice_date
    
    @api.multi
    def markinvoiced(self):
        
        self.ensure_one()  
        self.invoiced = True
    
    @api.multi
    def invoice(self):
        
        self.ensure_one()  
        self.invoiced = True
        
        view_id = self.env['ir.model.data'].get_object_reference('sale', 'view_sale_advance_payment_inv')[1]
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.advance.payment.inv',
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': view_id,
            'target': 'new',
            'context': {'active_ids': [self.sale_order_id.id], 'active_model':'sale.order'}
        }
        
    
    @api.model
    def create(self, values):    
        
        if('sale_order_id' in values and values['sale_order_id']):
            order = self.env['sale.order'].browse(values['sale_order_id'])[0]

            if(order.project_id):

                if(not 'analytic_account_id' in values or not values['analytic_account_id']):
                    values['analytic_account_id'] = order.project_id.id

                if(not 'date_from' in values or not values['date_from']):
                    values['date_from'] = order.project_id.date_start

                if(not 'date_to' in values or not values['date_to']):
                    values['date_to'] = order.project_id.date

            else:
                raise Warning(_("Current order is not related to any analytic account. Please provide one before inserting budget lines"))

        res = super(BudgetLine,self).create(values)

        return res

        

