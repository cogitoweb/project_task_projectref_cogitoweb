# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions, tools

import pprint
#Import logger
import logging
#Get the logger
_logger = logging.getLogger(__name__)

class Task(models.Model):

    _inherit = 'project.task'
    
    @api.depends('planned_hours', 'user_id')
    def compute_cost(self):
        
        # ricava il costo orario dal contratto
        for t in self:
            resource = self.env['resource.resource'].sudo().search([('user_id','=',t.user_id.id)])
            employee = self.env['hr.employee'].sudo().search([('resource_id','=',resource.id)])
            cost = 0

            if(resource and employee and employee.contract_id):
                hour_cost = employee.contract_id.wage
                cost = hour_cost * t.planned_hours

            t.cost = cost 

            
    @api.depends('sale_line_id', 'sale_line_id.price_unit', 'points')
    def compute_price(self):
        
        for t in self:
            
            #
            ## based on points
            #
            if(t.points):
                t.price = t.an_acc_by_prj.point_unit_price * t.points
            #
            ## base on sale offer
            #
            else:
                row_price = 0
                price = 0

                if(t.sudo().sale_line_id.id):
                    
                    row_price = t.sale_line_id.price_unit * t.sale_line_id.product_uom_qty
                    self._cr.execute("select sum(cost) from project_task where sale_line_id = %s and stage_id <> 8" %
                                            str(t.sale_line_id.id))
                    r = self._cr.fetchone()
                    total_cost = float(r[0]) if len(r) and r[0] else 0

                    if(total_cost):
                        price = (t.cost/total_cost) * row_price

                t.price = price  
                 
    ####        
    ####  FIELDS        
    ####        

    points = fields.Integer(string='Points')
    
    project_ref_id = fields.Many2one('project.project', 'Project reference')
    
    an_acc_by_prj = fields.Many2one('account.analytic.account', string="Contract/Analytic",
                                                     related='project_id.analytic_account_id',readonly=True)
    an_acc_by_prj_ref = fields.Many2one('account.analytic.account', string="Contract/Analytic reference",
                                                         related='project_ref_id.analytic_account_id',readonly=True)
    
    price = fields.Float(required=True, default=0, readonly=True, compute=compute_price, store=True, compute_sudo=True)
    
    cost = fields.Float(required=True, default=0, readonly=True, compute=compute_cost, store=True, compute_sudo=True)
    
    effective_cost = fields.Float(required=True, default=0, readonly=True, store=True)
    
    ms_project_data = fields.Text()
    
    def _get_sale_order_line(self, cr, uid, sale_line_id, context=None):
        sale_order_line = self.pool.get('sale.order.line')
        sos = sale_order_line.sudo().browse(cr, uid, [sale_line_id], context=context)
        so = sos and sos[0] or False
        return so
    
    def _get_current_task(self, cr, uid, ids, context=None):
        task = self.pool.get('project.task')
        tks = task.browse(cr, uid, ids, context=context)
        t = tks and tks[0] or False
        return t
    
    def write(self, cr, uid, ids, values, context=None):
        """ When populating sale_line_id create procurment """
        res = super(Task, self).write(cr, uid, ids, values, context=context)
        
        t = self._get_current_task(cr, uid, ids, values)

        if values.get('sale_line_id') and t and (t.procurement_id.id == False):
            
            procurement = self.pool.get('procurement.order')
            sale_order_line = self._get_sale_order_line(cr, uid, values.get('sale_line_id'))
            
            procurement_id = procurement.create(cr, uid, {
                'origin': '%s' % ('AUTO PR FROM ' + t.name),
                'product_uom': sale_order_line.product_uom.id,
                'product_uos_qty': sale_order_line.product_uos_qty,
                'product_uom_qty': sale_order_line.product_uos_qty,
                'product_uos': sale_order_line.product_uos.id,
                'company_id': sale_order_line.company_id.id,
                'product_qty': 1,
                'name': '%s' % ('PR FROM ' + t.name),
                'product_id': sale_order_line.product_id.id,
                'date_planned': t.date_deadline or fields.Date.today(),
                'sale_line_id': sale_order_line.id,
                'task_id': t.id,
            },context=context)
            
            self.write(cr, uid, [t.id], {'procurement_id': procurement_id}, context=context)
            
        return res
    
    # fix defect on date_deadline setup
    # and date gant copy on date_ends
    def onchange_date_deadline(
            self, cr, uid, ids, date_end, date_deadline, context=None):
        if not date_end or (date_end[:10] == self.browse(
                cr, uid, ids, context=context).date_deadline):
            
            # set hour at the end of the day but not too close to midnight
            outdate = date_deadline + ' 19:00:00' if date_deadline else False     
            return {'value': {'date_end': outdate}}