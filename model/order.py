# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions, tools

import pprint
#Import logger
import logging
#Get the logger
_logger = logging.getLogger(__name__)

class OrderLine(models.Model):

    _inherit = 'sale.order.line'
    
    tasks_ids = fields.One2many('project.task', string="Related Tasks", compute="compute_tasks_ids")
    
    tasks_count = fields.Integer(compute="compute_tasks_ids", string="Tasks")
    
    @api.one
    def compute_tasks_ids(self):
        
        related_recordset = self.env["project.task"].sudo().search([("sale_line_id", "=", self.id)])
        self.tasks_ids = related_recordset
        self.tasks_count = len(related_recordset)
        
    @api.onchange('price_unit')
    def compute_tasks_prices(self):
        
        for t in self.tasks_ids:
            t.compute_price()

class Order(models.Model):

    _inherit = 'sale.order'
    
    sale_offer_markup = fields.Float(related='project_id.sale_offer_markup', readonly=True)
   
    real_project_id = fields.Many2one('project.project', string="Project", related="project_id.project_id", readonly=True)
    
    unrelated_task_ids = fields.One2many('project.task', string="Related Tasks", compute="compute_unrelated_task_ids")
    
    @api.one
    def compute_unrelated_task_ids(self):
        
        unrelated_recordset = self.env["project.task"].sudo().search([
            ("sale_line_id", "=", False), ("project_id", "=", self.real_project_id.id)])
        self.unrelated_task_ids = unrelated_recordset
    
    @api.multi
    def calculate_project_costs(self):
        
        for l in self.order_line:
            line_cost = 0
        
            for t in l.tasks_ids:
                t.sudo().compute_price()
                line_cost = t.cost + line_cost
                
            if(line_cost>0):
                l.purchase_price = line_cost
                l.price_unit = line_cost * self.sale_offer_markup
            

        