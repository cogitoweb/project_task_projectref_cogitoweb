# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2017 2z@cogito
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)

class Project(models.Model): 
    
    _inherit = 'project.project'
    
    total_points = fields.Integer(compute='compute_total_points', store=True)
    used_points = fields.Integer(compute='compute_total_points', store=True)
    locked_points = fields.Integer(compute='compute_total_points', store=True)
    free_points = fields.Integer(compute='compute_total_points', store=True)

    @api.model
    def _needaction_domain_get(self):
        return []

    @api.depends('tasks.points', 'tasks.stage_id')
    def compute_total_points(self):
        for record in self:
            
            ## one liner
            # sum(task.points for task in record.tasks)
            
            tot = 0
            used = 0
            locked = 0
            free = 0
            
            for task in record.tasks:
                
                if task.points > 0:
                    if task.stage_id.id not in [7,8]: #not done or cancelled
                        locked = locked + task.points
                    elif task.stage_id.id in [7]: #only done
                        used = used + task.points
                elif task.points < 0:
                    if task.stage_id.id in [7]: #only done
                            tot = tot - task.points

            free = tot - (used + locked)
            
            record.total_points = tot
            record.used_points = used
            record.locked_points = locked
            record.free_points = free
