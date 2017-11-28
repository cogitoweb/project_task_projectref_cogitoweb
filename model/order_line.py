# -*- coding: utf-8 -*-
from openerp import models, fields, api, exceptions, tools

import pprint
import logging
_logger = logging.getLogger(__name__)

class OrderLine(models.Model):

    _inherit = 'sale.order.line'
    
    project_id = fields.Many2one('project.project', string="Related Project")
    fixed_price = fields.Boolean(default=False)
    tasks_ids = fields.One2many('project.task', string="Related Tasks", compute="compute_tasks_ids")
    tasks_count = fields.Integer(compute="compute_tasks_ids", string="Tasks")
    
    @api.one
    def compute_tasks_ids(self):
        
        related_recordset = self.env["project.task"].sudo().search([("sale_line_id", "=", self.id)])
        self.tasks_ids = related_recordset
        self.tasks_count = len(related_recordset)
        
    @api.onchange('price_unit')
    def compute_tasks_prices(self):
        
        for t in self.sudo().tasks_ids:
            t.compute_price()
