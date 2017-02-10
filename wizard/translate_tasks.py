# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp import exceptions
from openerp.exceptions import Warning

_logger = logging.getLogger(__name__)


class TranslateTasks(models.TransientModel):
	_name = 'translate.tasks'

	days = fields.Integer('Days to translate')

	@api.one
	def translate_tasks(self, context=None):

        if not context.project_id:
            raise Warning(_('Project is mandatory'))
            
        # esegui query diretta
		####################################
        
        query_string = """update project_task set 
                            date_start = date_deadline + interval '%s' day 
                            date_end = date_end + interval '%s' day 
                            date_deadline = date_deadline + interval '%s' day 
                            where priject_id = %s
                            and stage_id not in (select id from project_task_type where closed = true)
                            """
        
		self.env.cr.execute(query_string, (self.days, self.days, self.days, context.project_id))

		return {'type': 'ir.actions.act_window_close'}




