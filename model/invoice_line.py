# -*- coding: utf-8 -*-
from openerp import models, fields, api, exceptions, tools

import pprint
import logging
_logger = logging.getLogger(__name__)


class InvoiceLine(models.Model):

    _inherit = 'account.invoice.line'
    
    # Fields

    order_line_id = fields.Many2one(
        'sale.order.line', 'Order line reference',
    ) 