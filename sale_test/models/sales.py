from odoo import models, _
from odoo.tools import Markup


# class SaleOrder(models.Model):
#     _inherit = 'sale.order'
#
#     def write(self, vals):
#         for order in self:
#             old_amount_total = order.amount_total
#             old_payment_term = order.payment_term_id.name or ""
#
#             res = super(SaleOrder, order).write(vals)
#
#             messages = []
#
#             # Track amount_total change
#             if 'order_line' in vals or 'amount_untaxed' in vals or 'amount_tax' in vals:
#                 new_amount_total = order.amount_total
#                 if order.state != 'sale' and new_amount_total != old_amount_total:
#                     msg = _(
#                         "Total Amount: %(old)s → %(new)s",
#                         old="%.2f" % old_amount_total,
#                         new="%.2f" % new_amount_total
#                     )
#                     messages.append(Markup("<li>") + msg + Markup("</li>"))
#
#             # Track payment_term_id change
#             if 'payment_term_id' in vals:
#                 new_payment_term = self.env['account.payment.term'].browse(vals['payment_term_id']).name or ""
#                 if old_payment_term != new_payment_term:
#                     msg = _(
#                         "Payment Term: %(old)s → %(new)s",
#                         old=old_payment_term,
#                         new=new_payment_term
#                     )
#                     messages.append(Markup("<li>") + msg + Markup("</li>"))
#
#             if messages:
#                 order.message_post(body=Markup("<ul>") + Markup("").join(messages) + Markup("</ul>"))
#
#         return res
