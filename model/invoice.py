# -*- coding: utf-8 -*-
from openerp import models, fields, api, exceptions, tools

import pprint
import logging
_logger = logging.getLogger(__name__)


class Invoice(models.Model):

    _inherit = 'account.invoice'
    
    ## guess related order
    ##
    @api.depends('origin')
    def _get_related_order(self):

        for rd in self:
            order = self.env['sale.order'].search([('name','=',rd.origin)],limit=1)
            rd.order_reference_id = order[0] if order else None

    @api.multi
    def _get_inverse_related_order(self):
        pass

    # Fields

    order_reference_id = fields.Many2one(
        'sale.order', 'Order reference', compute=_get_related_order,
        inverse=_get_inverse_related_order, readonly=True, store=False
    )

    # override to manage related tasks
    # of billing plans
    @api.multi
    def unlink(self):
        
        for record in self:
            task_to_reset = self.env['project.task'].sudo().search(
                [
                    ('billing_plan', '=', True),
                    ('invoice_id', '=', record.id),
                    ('invoiced', '=', True),
                ]
            )

            task_to_reset.marktoinvoice()
        # end for
    
        return super(Invoice, self).unlink()
