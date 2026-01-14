from odoo import models, fields, api
from odoo import models, fields, api
from collections import defaultdict
from datetime import timedelta
from markupsafe import Markup

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare, float_round, format_date, groupby

SALE_ORDER_STATE = [
    ('draft', "Quotation"),
    ('sent', "Quotation Sent"),
    ('sale', "Sales Order"),
    ('cancel', "Cancelled"),
]


class SaleOrder(models.Model):
    _inherit = "sale.order"

    amount_total = fields.Monetary(string="Total", store=True, compute='_compute_amounts', tracking=True)

    # def _track_subtype(self, init_values):
    #     self.ensure_one()
    #     if 'amount_total' in init_values:
    #         return self.env.ref('my_sale_custom.mt_amount_changed')  # استخدم ID تبع XML
    #     return super()._track_subtype(init_values)
    # @api.depends('order_line.price_subtotal', 'order_line.price_tax', 'order_line.price_total')
    # def _compute_amounts(self):
    #     """Compute the total amounts of the SO."""
    #     for order in self:
    #         order = order.with_company(order.company_id)
    #         order_lines = order.order_line.filtered(lambda x: not x.display_type)
    #
    #         # Save old values
    #         old_untaxed = order.amount_untaxed
    #         old_tax = order.amount_tax
    #
    #         if order.company_id.tax_calculation_rounding_method == 'round_globally':
    #             tax_results = order.env['account.tax']._compute_taxes([
    #                 line._convert_to_tax_base_line_dict()
    #                 for line in order_lines
    #             ])
    #             totals = tax_results['totals']
    #             amount_untaxed = totals.get(order.currency_id, {}).get('amount_untaxed', 0.0)
    #             amount_tax = totals.get(order.currency_id, {}).get('amount_tax', 0.0)
    #         else:
    #             amount_untaxed = sum(order_lines.mapped('price_subtotal'))
    #             amount_tax = sum(order_lines.mapped('price_tax'))
    #
    #         # Assign new values
    #         order.amount_untaxed = amount_untaxed
    #         order.amount_tax = amount_tax
    #
    #         order.amount_total = amount_untaxed + amount_tax
    #
    #         # Post message only if values changed
    #         # if old_untaxed != amount_untaxed or old_tax != amount_tax:
    #         #     msg = f"Amounts changed:\n"
    #         #     if old_untaxed != amount_untaxed:
    #         #         msg += f"- Untaxed: {old_untaxed} -> {amount_untaxed}\n"
    #         #     if old_tax != amount_tax:
    #         #         msg += f"- Tax: {old_tax} -> {amount_tax}\n"
    #         #     order.message_post(body=msg)

    def write(self, vals):
        for order in self:
            old_amount_total = order.amount_total
            old_payment_term = order.payment_term_id.name or ""
            res = super(SaleOrder, order).write(vals)

            messages = []

            # Track amount_total change
            if 'order_line' in vals or 'amount_untaxed' in vals or 'amount_tax' in vals:
                new_amount_total = order.amount_total
                if order.state != 'sale' and new_amount_total != old_amount_total:
                    msg = _(
                        "Total Amount: %(old)s → %(new)s",
                        old="%.2f" % old_amount_total,
                        new="%.2f" % new_amount_total
                    )
                    messages.append(Markup("<li>") + msg + Markup("</li>"))

            # Track payment_term_id change
            if 'payment_term_id' in vals:
                new_payment_term = order.payment_term_id.name or ""
                if old_payment_term != new_payment_term:
                    msg = _(
                        "Payment Term: %(old)s → %(new)s",
                        old=old_payment_term,
                        new=new_payment_term
                    )
                    messages.append(Markup("<li>") + msg + Markup("</li>"))

            if messages:
                order.message_post(body=Markup("<ul>") + Markup("").join(messages) + Markup("</ul>"))
        for order in self:
            old_amount_total = order.amount_total

            if 'order_line' in vals or 'amount_untaxed' in vals or 'amount_tax' in vals:
                new_amount_total = order.amount_total
                if order.state != 'sale' and new_amount_total != old_amount_total:
                    msg = Markup("<li>") + _(
                        "Total Amount: %(old)s → %(new)s",
                        old="%.2f" % old_amount_total,
                        new="%.2f" % new_amount_total
                    ) + Markup("</li>")
                    order.message_post(
                        body=Markup("<ul>") + msg + Markup("</ul>")

                    )

        return res


from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare
from markupsafe import Markup


class AddTitleFieSld(models.Model):
    _inherit = 'sale.order.line'

    @api.model
    def create(self, vals):
        line = super().create(vals)

        if line.order_id and line.name:
            msg = Markup(
                _("<b>New Sale Order Line Added:</b><br/>") +
                _("Description: %s") % line.name
            )
            line.order_id.message_post(body=msg)

        return line

    def write(self, values):
        if 'display_type' in values and self.filtered(lambda line: line.display_type != values.get('display_type')):
            raise UserError(
                _("You cannot change the type of a sale order line. Instead you should delete the current line and create a new line of the proper type.")
            )

        # تحقق إذا كان أي من هذه الحقول قد تغيّر
        if any(key in values for key in ['product_uom_qty', 'discount', 'price_unit', 'product_uom', 'name']):
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            self.filtered(lambda r: (
                    r.state in ['draft','sent', 'sale'] and (
                    ('product_uom_qty' in values and float_compare(r.product_uom_qty, values['product_uom_qty'],
                                                                   precision_digits=precision) != 0)
                    or 'discount' in values
                    or 'price_unit' in values
                    or 'product_uom' in values
                    or 'name' in values
            )
            ))._update_line_quantitys(values)

        return super(AddTitleFieSld, self).write(values)

    # def _update_line_quantity(self, values):
    #     orders = self.mapped('order_id')
    #     for order in orders:
    #         order_lines = self.filtered(lambda x: x.order_id == order)
    #         msg = Markup("<b>%s</b><ul>") % _("The ordered quantity has been updated.")
    #         for line in order_lines:
    #             if 'product_id' in values and values['product_id'] != line.product_id.id:
    #                 # tracking is meaningless if the product is changed as well.
    #                 continue
    #             msg += Markup("<li> %s: <br/>") % line.product_id.display_name
    #             msg += _(
    #                 "Ordered Quantity: %(old_qty)s -> %(new_qty)s",
    #                 old_qty=line.product_uom_qty,
    #                 new_qty=values["product_uom_qty"]
    #             ) + Markup("<br/>")
    #             if line.product_id.type in ('consu', 'product'):
    #                 msg += _("Delivered Quantity: %s", line.qty_delivered) + Markup("<br/>")
    #             msg += _("Invoiced Quantity: %s", line.qty_invoiced) + Markup("<br/>")
    #
    #             if any(key in values for key in ["price_unit", "discount", "product_uom", "name"]):
    #                 msg += Markup("<b>%s</b><ul>") % _("Line changes:")
    #                 for line in order_lines:
    #                     if 'product_id' in values and values['product_id'] != line.product_id.id:
    #                         continue
    #                     msg += Markup("<li> %s:<br/>") % line.product_id.display_name
    #                     if "price_unit" in values:
    #                         msg += _(
    #                             "Unit Price: %(old)s -> %(new)s",
    #                             old=line.price_unit,
    #                             new=values["price_unit"]
    #                         ) + Markup("<br/>")
    #                     if "discount" in values:
    #                         msg += _(
    #                             "Discount: %(old)s -> %(new)s",
    #                             old=line.discount,
    #                             new=values["discount"]
    #                         ) + Markup("<br/>")
    #
    #                     if "name" in values:
    #                         msg += _(
    #                             "Description: %(old)s -> %(new)s",
    #                             old=line.name,
    #                             new=values["name"]
    #                         ) + Markup("<br/>")
    #                 msg += Markup("</ul>")
    #         msg += Markup("</ul>")
    #         order.message_post(body=msg)

    def _update_line_quantitys(self, values):
        orders = self.mapped('order_id')

        for order in orders:
            order_lines = self.filtered(lambda x: x.order_id == order)
            msg = ""

            # الكمية
            if "product_uom_qty" in values and values.get('state') != 'sale':
                msg += Markup("<b>%s</b><ul>") % _("The ordered quantity has been updated.")
                for line in order_lines:
                    if 'product_id' in values and values['product_id'] != line.product_id.id:
                        continue
                    msg += Markup("<li> %s:<br/>") % line.product_id.display_name
                    msg += _(
                        "Quantity: %(old_qty)s -> %(new_qty)s",
                        old_qty=line.product_uom_qty,
                        new_qty=values["product_uom_qty"]
                    ) + Markup("<br/>")
                    if line.product_id and line.product_id.type in ('consu', 'product'):
                        msg += _("Delivered Quantity: %s", line.qty_delivered) + Markup("<br/>")
                msg += Markup("</ul>")

            # الحقول الأخرى
            if any(key in values for key in ["price_unit", "discount", "product_uom", "name"]):
                msg += Markup("<b>%s</b><ul>") % _("Line changes:")
                for line in order_lines:
                    if 'product_id' in values and values['product_id'] != line.product_id.id:
                        continue
                    msg += Markup("<li> %s:<br/>") % line.product_id.display_name
                    if "price_unit" in values:
                        msg += _(
                            "Unit Price: %(old)s -> %(new)s",
                            old=line.price_unit,
                            new=values["price_unit"]
                        ) + Markup("<br/>")
                    if "discount" in values:
                        msg += _(
                            "Discount: %(old)s -> %(new)s",
                            old=line.discount,
                            new=values["discount"]
                        ) + Markup("<br/>")
                    if "product_uom" in values:
                        old_uom = line.product_uom.name or ""
                        new_uom = self.env['uom.uom'].browse(values["product_uom"]).name or ""
                        msg += _(
                            "UoM: %(old)s -> %(new)s",
                            old=old_uom,
                            new=new_uom
                        ) + Markup("<br/>")
                    if "name" in values:
                        msg += _(
                            "Description: %(old)s -> %(new)s",
                            old=line.name,
                            new=values["name"]
                        ) + Markup("<br/>")
                msg += Markup("</ul>")

            # نشر الرسالة
            if msg:
                order.message_post(body=msg)

# class SaleOrder(models.Model):
#     _inherit = 'sale.order'
#
#     state = fields.Selection(
#         selection=SALE_ORDER_STATE,
#         string="Status",
#         readonly=True, copy=False, index=True,
#         tracking=1,
#         default='draft')
#     locked = fields.Boolean(default=False, copy=False, help="Locked orders cannot be modified.")
#
#     def write(self, vals):
#         res = super().write(vals)
#         for order in self:
#             if order.state in ['draft', 'sent']:  # i.e. still a quotation
#                 order.message_post(body="✏️ Quotation updated.")
#         return res
#
# class SaleOrderLine(models.Model):
#     _inherit = 'sale.order.line'
#
#     tax_totals = fields.Binary(compute='_compute_tax_totals',  tracking = True, exportable=False)
#
#     product_uom_qty = fields.Float(
#         string="Quantity",
#         compute='_compute_product_uom_qty',
#         digits='Product Unit of Measure',
#         default=1.0,
#         store=True,
#         readonly=False,  # Editable "trick" for computed fields
#         required=True,
#         precompute=True,
#     tracking = True
#     )

# class AddTitleField(models.Model):
#     _inherit = 'sale.order'
#
#     title = fields.Char(string="Title")
#
#     @api.onchange('partner_id')
#     def _compute_related_activities(self):
#         # for order in self:
#             l = self.env['mail.activity'].search([
#                 # ('res_model', '=', 'sale.order'),
#                 ('id', '=', 195),
#             ])
#             print(l)
#
#
#
# class ResUsers(models.Model):
#     _inherit = 'res.users'
#     appbar_image = fields.Binary("Appbar Image")
