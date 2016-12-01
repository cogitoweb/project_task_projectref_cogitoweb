# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions, tools 

class project_task_projectref_cogitoweb(models.Model):

    _inherit = 'project.task'
    
    project_ref_id = fields.Many2one('project.project', 'Project reference')
    
    price = fields.Float(required=True, default=0)
    
    cost = fields.Float(required=True, default=0)
