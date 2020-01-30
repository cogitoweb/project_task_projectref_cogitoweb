# -*- coding: utf-8 -*-
""" override task """

import pprint
import logging
from dateutil import parser
import re
from datetime import datetime, date, timedelta

from openerp.tools.translate import _
from openerp import models, fields, api, exceptions, tools
_logger = logging.getLogger(__name__)


class Task(models.Model):
    """ override task """

    _inherit = 'project.task'
    _stage_id_fatturazione = 5002
    _stage_id_specifica = 2
    _stage_id_annullo = 8
    _stage_id_done = 7

    @api.model
    def _needaction_domain_get(self):
        """ _needaction_domain_get remove unused counter on menu """
        return []

    @api.depends('sale_order_state', 'invoiced', 'stage_id')
    def compute_can_be_invoiced(self):
        """ compute_can_be_invoiced """
        for t in self:
            t.can_be_invoiced = (t.sale_order_state == 'manual' and
                                 (t.invoiced == True or not t.stage_id or t.stage_id.id not in [self._stage_id_fatturazione]))

    @api.depends('planned_hours', 'user_id')
    def compute_cost(self):
        """ ricava il costo orario dal contratto  """
        for task in self:
            resource = self.env['resource.resource'].sudo().search(
                [
                    ('user_id', '=', task.user_id.id)
                ]
            )
            employee = self.env['hr.employee'].sudo().search(
                [
                    ('resource_id', '=', resource.id)
                ]
            )
            cost = 0

            if resource and employee and employee.contract_id:
                hour_cost = employee.contract_id.wage
                cost = hour_cost * task.planned_hours

            task.cost = cost

    @api.depends('direct_sale_line_id', 'direct_sale_line_id.price_unit', 'cost', 'points')
    def compute_price(self):
        """ ricalcola il prezzo basato sui punti o sulla riga di offerta  """
        for task in self.sudo():
            if task.points:
                """
                ## based on points
                """
                task.price = task.an_acc_by_prj.point_unit_price * task.points
            else:
                """
                    ## base on sale offer
                """
                row_price = 0
                price = 0

                if(task.direct_sale_line_id and
                   isinstance(task.direct_sale_line_id.id, (int, long))):

                    line = task.direct_sale_line_id

                    row_price = line.price_unit * line.product_uom_qty
                    self._cr.execute("select sum(cost), case when count(id) > 0 then count(id) else 1 end  from project_task "
                                     " where direct_sale_line_id = %s and stage_id <> %s" %
                                     (line.id, self._stage_id_annullo))
                    record = self._cr.fetchone()

                    _logger.info(pprint.pformat(record))

                    """ costo calcolato in proporzione al prezzo dei task
                    o in proporzione al loro numero se il prezzo totale è 0 """
                    cost_factor = task.cost/float(record[0]) if record[0] else 1/float(record[1])

                    _logger.info("recalc cost/price %s" % cost_factor)

                    price = cost_factor * row_price

                task.price = price

    def _default_invoice_date_cache(self):
        if 'budget_line_cache_invoice_date' in self.cache:
            return self.cache['budget_line_cache_invoice_date']
        return False

    def _default_planned_amount_cache(self):
        if 'budget_line_cache_planned_amount' in self.cache:
            return self.cache['budget_line_cache_planned_amount']
        return False

    """
        ####        
        ####  FIELDS        
        ####        
    """
    points = fields.Integer(string='Points')
    project_ref_id = fields.Many2one('project.project', 'Project reference', index=True)
    an_acc_by_prj = fields.Many2one('account.analytic.account',
                                    string="Contract/Analytic",
                                    related='project_id.analytic_account_id',
                                    readonly=True
                                   )
    an_acc_by_prj_ref = fields.Many2one('account.analytic.account',
                                        string="Contract/Analytic reference",
                                        related='project_ref_id.analytic_account_id',
                                        readonly=True
                                       )
    price = fields.Float(required=True, default=0, readonly=True,
                         compute=compute_price,
                         store=True,
                         compute_sudo=True
                        )
    cost = fields.Float(required=True, default=0, readonly=True, compute=compute_cost, store=True, compute_sudo=True)
    effective_cost = fields.Float(required=True, default=0, readonly=True, store=True)
    ms_project_data = fields.Text()

    direct_sale_line_id = fields.Many2one('sale.order.line', index=True)
    product_id = fields.Many2one('product.product', index=True)
    sale_order_id = fields.Many2one('sale.order', index=True)
    sale_order_state = fields.Selection(related='sale_order_id.state')

    billing_plan = fields.Boolean(defaut=False)
    can_be_invoiced = fields.Boolean(compute=compute_can_be_invoiced)
    invoiced = fields.Boolean(defaut=False, index=True)
    invoice_date = fields.Date(index=True)
    invoice_amount = fields.Float()

    invoice_id = fields.Many2one(
        'account.invoice',
        index=True
    )

    # used in interface && invoice procedure
    @api.multi
    def markinvoiced(self):

        self.write(
            {
                'invoiced': True,
                'stage_id': self._stage_id_done
            }
        )

    # used in invoice unlink() && interface
    @api.multi
    def marktoinvoice(self):

        self.write(
            {
                'invoiced': False,
                'stage_id': self._stage_id_fatturazione,
                'invoice_id': False
            }
        )

    @api.multi
    def manual_invoice(self):

        self.ensure_one()
        self.invoiced = True
        self.stage_id = self._stage_id_done

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

    # imposta prodotto ed offerta
    # se direct_sale_line_id popolato
    def _auto_set_product(self, values):

        ### auto set product if direct_sale_line_id
        if 'direct_sale_line_id' in values:

            product_id = False
            if values['direct_sale_line_id']:

                line = self.env['sale.order.line'].sudo().browse(
                            values['direct_sale_line_id']
                        )

                _logger.info("line IS %s" % line)
                _logger.info("product line IS %s" % line.product_id)

                product_id = line.product_id.id if line.product_id else False

                values['product_id'] = product_id
                values['sale_order_id'] = line.order_id.id

        # end auto set product

        ### set auto invoiced
        if 'invoice_id' in values:

            values['invoiced'] = True if values['invoice_id'] else False
        # end auto invoiced

        return values

    @api.multi
    def write(self,values):
        """ override write """
        values = self.populate_billing_task(values, 'write')

        values = self._auto_set_product(values)

        """ DO NOT create procurment """
        res = super(Task, self).write(values)

        return res

    @api.model
    def create(self, values):
        """ override create """
        values = self.populate_billing_task(values, 'create')

        values = self._auto_set_product(values)

        return super(Task, self).create(values)

    def populate_billing_task(self, values, mode):
        """ gestione per righe di fatturazione
            nel caso di creazione task da ordine  """

        if('billing_plan' in values and values['billing_plan']):

            if(not 'date_deadline' in values or not values['date_deadline']):
                values['date_deadline'] = values['invoice_date']
            else:
                values['invoice_date'] = values['date_deadline']

            # nomi e date da ordine
            try:
                values['name'] = 'Fatturazione del %s' % parser.parse(values['invoice_date']).strftime("%d/%m/%Y")
            except:
                values['name'] = 'Fatturazione del %s' % values['invoice_date'].strftime("%d/%m/%Y")

            ## stato da fatturare (5002)
            values['stage_id'] = self._stage_id_fatturazione

            values['date_start'] = values['invoice_date']
            values['date_end'] = values['invoice_date']

            order = self.env['sale.order'].browse(values['sale_order_id'])
            config_analytic_account_administration = self.env['ir.config_parameter'].search([('key', '=', 'internal_analytic_account_administration_id')], limit=1)
            internal_analytic_account_administration = self.env['account.analytic.account'].browse([int(config_analytic_account_administration.value)])

            values['user_id'] = internal_analytic_account_administration.manager_id.id
            values['reviewer_id'] = internal_analytic_account_administration.manager_id.id

            ## rif al progetto
            values['project_id'] = internal_analytic_account_administration.project_id.id
            values['project_ref_id'] = order.real_project_id.id
            values['partner_id'] = order.real_project_id.partner_id.id

        return values

    def onchange_date_deadline(
            self, cr, uid, ids, date_end, date_deadline, context=None):
        """ fix defect on date_deadline setup
            and date gant copy on date_ends """

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

    #
    # FATTURAZIONE
    #
    @api.multi
    def invoice_task(self):

        # costanti
        ACCOUNT_ID = 33
        PRODUCT_ACCOUNT_ID = 5342
        JOURNAL_ID = 1

        # counters
        invoice_count = 0

        # start check
        for record in self:

            # check sale_order_id
            if not record.billing_plan:

                raise Warning(
                    _("Task id %s is not part of a billing plan") % record.id
                )

            if not record.sale_order_id:

                raise Warning(
                    _("Task id %s does not have sale order") % record.id
                )

            if record.invoiced:

                raise Warning(
                    _("Task id %s seems to be already invoiced (or maybe forced...)") % record.id
                )

            if not record.invoice_amount:

                raise Warning(
                    _("Task id %s has no ivoice amount: what type of billing plan is this? :-)") % record.id
                )

            if not record.date_deadline:

                raise Warning(
                    _("Task id %s does not have deadline date") % record.id
                )

            if not record.an_acc_by_prj_ref:

                raise Warning(
                    _("Missing project ref or account ref in Task id %s") % record.id
                )

            sale_order = record.sale_order_id
            partner_id = sale_order.partner_id
            invoice_count += 1

            invoice = self.env['account.invoice'].create(
                {
                    'partner_id': partner_id.id,
                    'account_id': partner_id.property_account_receivable.id if \
                        partner_id.property_account_receivable else ACCOUNT_ID,
                    'journal_id': JOURNAL_ID,
                    'fiscal_position': partner_id.property_account_position.id if \
                        partner_id.property_account_position else False,
                    'order_reference_id': sale_order.id,
                    'origin': sale_order.name,
                    'date_invoice': record.date_deadline
                }
            )

            # add splitted lines
            line_to_invoce = []

            # search not invoiced lines
            for line in sale_order.order_line:

                line_amount_to_invoice = line.amount_to_invoice
                # append line with remaining amount
                if line_amount_to_invoice > 0:
                    line_to_invoce.append(
                        (line.id, line_amount_to_invoice)
                    )
            
            # get total of current invoice
            total_price_to_invoice = record.invoice_amount
            # get total of whole offer
            total_offer_price = sale_order.amount_untaxed

            for line in line_to_invoce:

                actual_line = sale_order.order_line.filtered(
                    lambda x: x.id == line[0]
                )

                taxes = []
                for t in actual_line.product_id.taxes_id:
                    taxes.append((4, t.id))
                
                # placeholder per date
                line_descr = actual_line.invoice_description if \
                   actual_line.invoice_description else actual_line.name
                # You can insert the following espression based on billing plan invoicing date:
                #   * #(#deadline_date#)# prints date in format gg/mm/aaaa
                #   * #(#deadline_date +(-) n#)#  add or removes days and prints date in format gg/mm/aaaa
                #   * #(#deadline_month#)# print month in longetxt italian format
                #   * #(#deadline_month +(-) n#)# add or removes months and print month in longetxt italian format
                matches = re.findall('#\(#deadline_(.*?)#\)#', line_descr, re.DOTALL)
                _logger.info("search for dates to replace")
                for match in matches:
                    _logger.info(match)

                # calcolo la proporzione di split del prezzo
                # in base alla distribuzione in offerta
                # prezzo_tot : prezzo_riga = prezzo_task : x
                line_price = actual_line.price_unit * actual_line.prduct_uom_qty
                prop_price = (line_price * total_price_to_invoice) / total_offer_price
                _logger.info(
                    """-------
                    total offer amount = %s
                    partial task amount = %s
                    line price = %s * quantity %s
                    full line price = %s
                    partial line price = %s
                    """ % (
                        total_offer_price,
                        total_price_to_invoice,
                        actual_line.price_unit, actual_line.prduct_uom_qty,
                        line_price,
                        prop_price
                    )
                )

                # il prezzo è il minimo tra il calcolato e il residuo
                final_price = min(line[1], prop_price)
                _logger.info("line final_price = %s (as min of %s and %s)" % (
                        final_price, line[1], prop_price
                    )
                )

                invoice_line_from_offer = self.env['account.invoice.line'].create(
                    {
                        'product_id': actual_line.product_id.id,
                        'account_id': actual_line.product_id.property_account_income.id if \
                            actual_line.product_id.property_account_income else PRODUCT_ACCOUNT_ID,
                        'invoice_id': invoice.id,
                        'uos_id': actual_line.product_id.uom_id.id,
                        'invoice_line_tax_id': taxes,
                        'price_unit': final_price,
                        'quantity': 1, # fixed to ONE
                        'name': line_descr,
                        'account_analytic_id': record.an_acc_by_prj_ref.id
                    }
                )
            # end of lines

            # includi arrotondamenti
            # sull'ultima riga
            # se mancano centesimi
            # a causa delle divisioni
            if invoice.amount_untaxed < total_price_to_invoice:
                invoice.invoice_line[-1].price_unit += total_price_to_invoice - invoice.amount_untaxed
                _logger.info(
                    "raise price of last line to %s" % invoice.invoice_line[-1].price_unit
                )

            # includi arrotondamenti se questo è l'ultimo task
            # del piano di fattturazione
            check_tasks_to_invoice = self.search(
                [
                    ('id', '!=', record.id),
                    ('sale_order_id', '=', sale_order.id),
                    ('invoice_id', '=', False)
                ]
            )
            # non ci sono altri task da fatturare
            if not check_tasks_to_invoice:
                # conto il già fatturato
                total_invoiced = sum(self.env['account.invoice'].search(
                    [
                        ('sale_order_id', '=', sale_order.id),
                    ]
                ).mapped('amount_untaxed'))

                # se differisce da totale offerta incremento
                # l'ultima riga
                if total_invoiced < total_offer_price:
                    invoice.invoice_line[-1].price_unit += total_offer_price - total_invoiced

                    _logger.info(
                        "final adjust to of last line to %s" % invoice.invoice_line[-1].price_unit
                    )
            # end if

            # register link
            record.invoice_id = invoice
            record.markinvoiced()
            # end of invoice

        return {
            'type': 'ir.actions.act_window.message',
            'title': _('Billing tasks invoicing'),
            'message': _(
                "Invoicing procedure completed:\n\n"
                "Generated %s invoices\n\n"
            ) % (invoice_count),
        }
