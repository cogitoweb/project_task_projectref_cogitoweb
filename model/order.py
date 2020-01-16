# -*- coding: utf-8 -*-
""" override sale order """

import pprint
import logging

from openerp import models, fields, api, exceptions, tools
from openerp.exceptions import Warning
_logger = logging.getLogger(__name__)

class Order(models.Model):
    """ override sale order """

    _inherit = 'sale.order'

    incipit = fields.Text()
    sale_offer_markup = fields.Float(related='project_id.sale_offer_markup')
    point_unit_price = fields.Float(related='project_id.point_unit_price')
    pre_paid = fields.Boolean(related='project_id.pre_paid')
    custom_invoicing_plan = fields.Boolean(related='project_id.custom_invoicing_plan')

    real_project_id = fields.Many2one('project.project', string="Project",
                                      related="project_id.project_id", readonly=True)
    unrelated_task_ids = fields.One2many('project.task', string="Related Tasks",
                                         compute="compute_unrelated_task_ids")
    task_to_invoice_ids = fields.One2many('project.task', 'sale_order_id', string="Billing plan")
    show_total = fields.Boolean(default=True)

    @api.multi
    def write(self, values):
        """ annullo eventuali task di fatturazione collegati
            all'annullamento dell'ordine
            annullo anche task non chiusi che contengono il nome ordine
            (fatturazione, gest produzione etc..) """

        if 'unrelated_task_ids' in values and len(self) == 1:
            for unreltask in values['unrelated_task_ids']:
                for task in self.unrelated_task_ids:
                    if task.id == unreltask[1]:
                        if unreltask[2] and 'direct_sale_line_id' in unreltask[2]:
                            task.direct_sale_line_id = unreltask[2]['direct_sale_line_id']
                        else:
                            task.direct_sale_line_id = False

        for order in self:
            if 'state' in values and values['state'] == 'cancel':

                order.task_to_invoice_ids.filtered(lambda record:
                                                   record.stage_id not in [7]).write(
                                                       {'stage_id': 8}
                                                    )

                order.unrelated_task_ids.filtered(lambda record: 
                                                  record.stage_id not in [7] and order.name in record.name).write(
                                                      {'stage_id': 8}
                                                  )

        res = super(Order, self).write(values)

        # check totali piano fatturazione
        for order in self:

            if order.custom_invoicing_plan:

                amount_total = round(order.amount_total, 2)
                invoice_total = round(
                    sum(line.invoice_amount for line in order.task_to_invoice_ids)
                )

                if amount_total != invoice_total:

                    raise Warning(
                        _('Total amount of order is different from the billing plan total amount')
                    )

        return res

    @api.one
    def compute_unrelated_task_ids(self):
        """ compute_unrelated_task_ids """

        if self.real_project_id:
            unrelated_recordset = self.env["project.task"].sudo().search(
                [
                    ("direct_sale_line_id", "=", False),
                    '|',
                    ("project_id", "=", self.real_project_id.id),
                    ("project_ref_id", "=", self.real_project_id.id)
                ]
            )
            self.unrelated_task_ids = unrelated_recordset

    @api.multi
    def calculate_project_costs(self):
        """ calculate_project_costs """

        for line in self.order_line:
            line_cost = 0

            for task in line.sudo().tasks_ids:
                task.compute_price()
                line_cost = task.cost + line_cost

            if not line.sudo().tasks_ids:
                line_cost = line.purchase_price

            update = {
                "purchase_price": line_cost,
                "price_unit": line_cost * self.sale_offer_markup if not line.fixed_price else line.price_unit
            }

            line.write(update)
