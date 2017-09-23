# -*- coding: utf-8 -*-

from openerp.tools.translate import _
from openerp import models, fields, api
from openerp import exceptions
from openerp.exceptions import Warning
import logging
import pprint

_logger = logging.getLogger(__name__)


class TranslateTasks(models.TransientModel):
    
    _name = 'translate.tasks'
    
    days = fields.Integer('Days to translate')
    new_stage = fields.Many2one('project.task.type', string='New stage to')
    
    @api.one
    def translate_tasks(self, context=None):
        
        if not context or not context.get('active_id', False):
            raise Warning(_('Project is mandatory'))

        new_stage_id = self.new_stage.id if self.new_stage else False
        
        # esegui query diretta  ####################################

        query_stage = ", stage_id = %s" % new_stage_id if new_stage_id else ""
        
        query_string = """update project_task set 
                            date_start = date_start + interval '%s' day, 
                            date_end = date_end + interval '%s' day,
                            date_deadline = date_deadline + interval '%s' day """ + query_stage + """
                            where project_id = %s and date_start is not null and date_end is not null and date_deadline is not null
                            and stage_id not in (select id from project_task_type where closed = true)
                            """
        
        self.env.cr.execute(query_string, (self.days, self.days, self.days, context.get('active_id', False)))
        
        return {'type': 'ir.actions.act_window_close'}
