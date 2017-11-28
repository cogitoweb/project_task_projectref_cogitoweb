# -*- coding: utf-8 -*-
from openerp import models, fields, api, exceptions, tools

import pprint
import logging
_logger = logging.getLogger(__name__)

class Order(models.Model):

    _inherit = 'sale.order'
    
    sale_offer_markup = fields.Float(related='project_id.sale_offer_markup', readonly=True)
    real_project_id = fields.Many2one('project.project', string="Project", related="project_id.project_id", readonly=True)
    unrelated_task_ids = fields.One2many('project.task', string="Related Tasks", compute="compute_unrelated_task_ids")
    task_to_invoice_ids = fields.One2many('project.task', 'sale_order_id', string="Billing plan")

    ## annullo eventuali task di fatturazione collegati all'annullamento dell'ordine
    ## annullo anche task non chiusi che contengono il nome ordine (fatturazione, gest produzione etc..)
    ## 
    @api.multi
    def write(self,values):

        if 'unrelated_task_ids' in values and len(self) == 1:
            
            for tt in values['unrelated_task_ids']:
                for t in self.unrelated_task_ids:
                    if(t.id == tt[1]):

                        if(tt[2] and 'sale_line_id' in tt[2]):
                            t.sale_line_id = tt[2]['sale_line_id']
                        else:
                            t.sale_line_id = False

        for o in self:
            if('state' in values and values['state'] == 'cancel'):
                
                o.task_to_invoice_ids.filtered(lambda record: record.stage_id not in [7]).write({'stage_id': 8})

                o.unrelated_task_ids.filtered(lambda record: record.stage_id not in [7] and o.name in record.name).write({'stage_id': 8})

        res = super(Order, self).write(values)

        return res

    @api.one
    def compute_unrelated_task_ids(self):

        if(self.real_project_id):
        
            unrelated_recordset = self.env["project.task"].sudo().search([
                ("sale_line_id", "=", False), '|', ("project_id", "=", self.real_project_id.id), ("project_ref_id", "=", self.real_project_id.id)])
            self.unrelated_task_ids = unrelated_recordset
    
    @api.multi
    def calculate_project_costs(self):
        
        for l in self.order_line:
            line_cost = 0
        
            for t in l.sudo().tasks_ids:
                t.compute_price()
                line_cost = t.cost + line_cost

            if not l.sudo().tasks_ids:
                line_cost = l.purchase_price

            update = {
                "purchase_price": line_cost,
                "price_unit": line_cost * self.sale_offer_markup if not l.fixed_price else l.price_unit
            }

            l.write(update)
            

