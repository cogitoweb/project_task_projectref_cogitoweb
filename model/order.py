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
        
        related_recordset = self.env["project.task"].search([("sale_line_id", "=", self.id)])
        self.tasks_ids = related_recordset
        self.tasks_count = len(related_recordset)
        
    @api.onchange('price_unit')
    def compute_tasks_prices(self):
        
        for t in self.tasks_ids:
            t.compute_price()

class Order(models.Model):

    _inherit = 'sale.order'
    
    @api.model
    def _default_internal_sale_offer_markup(self):
        self._cr.execute("select value from ir_config_parameter where key = 'internal_sale_offer_markup'")
        r = self._cr.fetchone()
        return float(r[0]) if r else 0
    
    project_markup = fields.Float(default=_default_internal_sale_offer_markup, readonly=True)
    real_project_id = fields.Many2one('project.project', string="Project", related="project_id.project_id", readonly=True)
    
    @api.multi
    def calculate_project_costs(self):
        
        for l in self.order_line:
            line_cost = 0
        
            for t in l.tasks_ids:
                t.compute_price()
                line_cost = t.cost + line_cost
                
            if(line_cost>0):
                l.purchase_price = line_cost
                l.price_unit = line_cost * self.project_markup
            

        