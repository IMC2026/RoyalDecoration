# models/crm_lead.py
from odoo import api, fields, models
from odoo.osv import expression

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    partner_arabic_name = fields.Char(
        related='partner_id.arabic_name',
        string='Arabic Name',
        store=True,
        index=True
    )

    def _get_lead_sale_order_domain(self):
        """Domain for sale orders that are confirmed (in 'sale' state)"""
        return [('state', '=', 'sale')]

    @api.depends('order_ids.state', 'order_ids.currency_id', 'order_ids.amount_untaxed',
                 'order_ids.date_order', 'order_ids.company_id')
    def _compute_sale_data(self):
        for lead in self:
            company_currency = lead.company_currency or self.env.company.currency_id

            # ONLY the total uses state='sale'
            sale_only = lead.order_ids.filtered(lambda so: so.state == 'sale')

            lead.sale_amount_total = sum(
                so.currency_id._convert(
                    so.amount_untaxed, company_currency, so.company_id, so.date_order or fields.Date.today()
                )
                for so in sale_only
            )

            # Keep the original counts/domains as-is:
            lead.quotation_count = len(lead.order_ids.filtered_domain(self._get_lead_quotation_domain()))
            lead.sale_order_count = len(lead.order_ids.filtered_domain(self._get_lead_sale_order_domain()))


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    partner_arabic_name = fields.Char(
        related='partner_id.arabic_name',
        string='Arabic Name',
        store=True,
        index=True
    )

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    partner_arabic_name = fields.Char(
        string='Arabic Name',
        related='partner_id.arabic_name',
        store=True,
        index=True,
    )

