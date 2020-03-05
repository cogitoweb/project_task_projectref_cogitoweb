from openerp import fields, models, api, _
from openerp.exceptions import ValidationError
import pprint

import logging
_logger = logging.getLogger(__name__)

class HrContract(models.Model):
    _inherit = 'hr.contract'
    
    # Fields

    monthly_wage = fields.Float(
        string="Monthly AVG wage", default=0.0
    )
    