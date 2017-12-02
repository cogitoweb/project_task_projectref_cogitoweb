# -*- coding: utf-8 -*-
""" override order line """

import pprint
import logging

from openerp import models, fields, api, exceptions, tools
_logger = logging.getLogger(__name__)

class OrderLine(models.Model):
    """ override order line """

    _inherit = 'sale.order.line'

    project_id = fields.Many2one('project.project', string="Related Project")
    fixed_price = fields.Boolean(default=False)
    tasks_ids = fields.One2many('project.task', 'direct_sale_line_id', string="Related Tasks")
    tasks_count = fields.Integer(compute="compute_tasks_ids", string="Tasks")

    @api.depends('tasks_ids')
    def compute_tasks_ids(self):
        """ recompute task count """
        for line in self:
            line.tasks_count = len(line.tasks_ids)
