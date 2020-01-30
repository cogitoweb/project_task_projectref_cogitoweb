# -*- coding: utf-8 -*-
""" override order line """

import pprint
import logging

from openerp import models, fields, api, exceptions, tools
_logger = logging.getLogger(__name__)

class OrderLine(models.Model):
    """ override order line """

    _inherit = 'sale.order.line'

    fixed_price = fields.Boolean(default=False)
    tasks_ids = fields.One2many(
        'project.task', 'direct_sale_line_id', string="Related Tasks"
    )
    tasks_count = fields.Integer(
        compute="compute_tasks_ids", string="Tasks"
    )
    invoice_description = fields.Text(
        string='Invoice Description',
        help="""Custom description can be used to describe product in invoice line
            (when using billing plan invoice procedure)
            You can insert the following espression based on billing plan invoicing date:
            * ###deadline_date### prints date in format gg/mm/aaaa
            * ###deadline_date +(-) n###  add or removes days and prints date in format gg/mm/aaaa
            * ###deadline_month### print month in longetxt italian format
            * ###deadline_month +(-) n### add or removes months and print month in longetxt italian format
        """
    )
    invoice_line_ids = fields.One2many(
        'account.invoice.line',
        'order_line_id',
        string="Related Invoice Lines"
    )
    amount_to_invoice = fields.Float(
        compute="compute_invoice_lines",
    )
    amount_invoiced = fields.Float(
        compute="compute_invoice_lines",
    )

    @api.depends('invoice_line_ids')
    def compute_invoice_lines(self):
        """ compute amout to invoice """

        for line in self:
            invoiced = sum(
                line.invoice_line_ids.mapped('price_subtotal')
            )

            line.amount_invoiced = invoiced
            line.amount_to_invoice = line.price_subtotal - invoiced
        #end for

    @api.depends('tasks_ids')
    def compute_tasks_ids(self):
        """ recompute task count """

        for line in self:
            line.tasks_count = len(line.tasks_ids)
        #end for
