from openerp import fields, models, api

class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'
    
    @api.model
    def _default_internal_point_unit_price(self):
        self._cr.execute("select value from ir_config_parameter where key = 'internal_point_unit_price'")
        r = self._cr.fetchone()
        return float(r[0]) if r else 0
    
    @api.model
    def _default_internal_sale_offer_markup(self):
        self._cr.execute("select value from ir_config_parameter where key = 'internal_sale_offer_markup'")
        r = self._cr.fetchone()
        return float(r[0]) if r else 0
    
    sale_offer_markup = fields.Float(default=_default_internal_sale_offer_markup)

    point_unit_price = fields.Float(
        default=_default_internal_point_unit_price
    )

    pre_paid = fields.Boolean(
        default=False
    )

    custom_invoicing_plan = fields.Boolean(
        default=False
    )
