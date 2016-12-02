from openerp import fields, models, api

class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'
    
    @api.model
    def _default_internal_point_unit_price(self):
        self._cr.execute("select value from ir_config_parameter where key = 'internal_point_unit_price'")
        r = self._cr.fetchone()
        return float(r[0]) if r else 0

    point_unit_price = fields.Float(default=_default_internal_point_unit_price)