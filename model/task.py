# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions, tools
from dateutil import parser
from datetime import datetime, timedelta

import pprint
#Import logger
import logging
#Get the logger
_logger = logging.getLogger(__name__)

class Task(models.Model):

    _inherit = 'project.task'

    @api.depends('milestone', 'project_id', 'project_ref_id')
    def compute_billing_project(self):
        
        # ricava il costo orario dal contratto
        for t in self:
            
            if(t.milestone):
                t.billing_project = t.project_id
            else:
                t.billing_project = t.project_ref_id
    
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

    @api.onchange('sale_line_id')
    def onchange_sale_line_id(self):

        self.sale_order_id = self.sale_line_id.order_id


    def _default_invoice_date_cache(self):
        
        if('budget_line_cache_invoice_date' in self.cache):
            return self.cache['budget_line_cache_invoice_date']
            
        return False
    
    def _default_planned_amount_cache(self):
        
        if('budget_line_cache_planned_amount' in self.cache):
            return self.cache['budget_line_cache_planned_amount']
            
        return False

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

    sale_order_id = fields.Many2one('sale.order')
    sale_order_state = fields.Selection(related='sale_order_id.state')

    billing_plan = fields.Boolean(defaut=False)
    billing_project = fields.Many2one('project.project', compute=compute_billing_project)
    invoiced = fields.Boolean(defaut=False)
    milestone = fields.Boolean(defaut=False)
    invoice_date = fields.Date()
    invoice_amount = fields.Float()

    @api.multi
    def markinvoiced(self):
        
        self.ensure_one()  
        self.invoiced = True
        self.stage_id = 8
    
    @api.multi
    def invoice(self):
        
        self.ensure_one()  
        self.invoiced = True
        self.stage_id = 7
        
        view_id = self.env['ir.model.data'].get_object_reference('sale', 'view_sale_advance_payment_inv')[1]
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.advance.payment.inv',
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': view_id,
            'target': 'new',
            'context': {'active_ids': [self.sale_order_id.id], 'active_model':'sale.order'}
        }
        
    @api.multi
    def write(self,values):

        values = self.populate_billing_task(values)

        """ When populating sale_line_id create procurment """
        res = super(Task, self).write(values)
        
        for t in self:
            if values.get('sale_line_id') and t and (t.procurement_id.id == False):
                
                sale_order_line = self.env['sale.order.line'].browse([values.get('sale_line_id')])

                procurement_id = self.env['procurement.order'].create({
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
                })
                
                t.write({'procurement_id': procurement_id})
            
        return res

    
    @api.model
    def create(self,values):

        values = self.populate_billing_task(values)

        return super(Task, self).create(values)

    # gestione per righe di fatturazione
    # nel caso di creazione task da ordine 
    def populate_billing_task(self, values):

        if('billing_plan' in values and values['billing_plan']):

            # nomi e date da ordine
            values['name'] = 'Fatturazione del %s' % parser.parse(values['invoice_date']).strftime("%d/%m/%Y")
            ## stato da fatturare
            values['stage_id'] = 5002

            if(not 'date_deadline' in values or not values['date_deadline']):
                values['date_deadline'] = values['invoice_date']
            else:
                values['invoice_date'] = values['date_deadline']
            values['date_start'] = values['invoice_date']
            values['date_end'] = values['invoice_date']

            order = self.env['sale.order'].browse(values['sale_order_id'])
            config_analytic_account_administration = self.env['ir.config_parameter'].search([('key', '=', 'internal_analytic_account_administration_id')], limit=1)
            internal_analytic_account_administration = self.env['account.analytic.account'].browse([int(config_analytic_account_administration.value)])

            values['user_id'] = internal_analytic_account_administration.manager_id.id
            values['reviewer_id'] = internal_analytic_account_administration.manager_id.id

            ## se milestone tutti i rif sono al progetto
            if(values['milestone']):
                values['project_id'] = order.real_project_id.id
                values['project_ref_id'] = internal_analytic_account_administration.project_id.id
            else:
                values['project_id'] = internal_analytic_account_administration.project_id.id
                values['project_ref_id'] = order.real_project_id.id

        return values
    
    # fix defect on date_deadline setup
    # and date gant copy on date_ends
    def onchange_date_deadline(
            self, cr, uid, ids, date_end, date_deadline, context=None):
        
        if not date_end or (date_end[:10] == self.browse(cr, uid, ids, context=context).date_deadline):
            
            # set hour at the end of the day but not too close to midnight
            date_end = date_deadline + ' 19:00:00' if date_deadline else False   
            
        # retrieve possible date start from db
        date_start = self.browse(cr, uid, ids, context=context).date_start
        
        # if date_end is set
        # and date start is not set so that odoo fills the field with now
        # or the db value is > than date_end
        if(date_end and ((not date_start and parser.parse(date_end) < datetime.now()) 
                            or (date_start and parser.parse(date_start) > parser.parse(date_end)))):
            date_start = parser.parse(date_end) - timedelta(hours=1)
            
        # conditional output
        out = {'date_end': date_end}
        
        if(date_start):
            out['date_start'] = date_start
        
        return {'value': out}
