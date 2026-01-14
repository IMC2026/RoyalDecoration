from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    allow_price_edit_user = fields.Boolean(
        string="Allow Price Edit (by current user)",
        compute="_compute_allow_price_edit_user",
        compute_sudo=False,  # يحسب حسب المستخدم الحالي
        store=False,
        help="True if the current user is in the 'Allow Price Edit (Sale Lines)' group."
    )

    @api.depends_context('uid')
    def _compute_allow_price_edit_user(self):
        has_group = self.env.user.has_group(
            "imc_sale_pricelist_edit.group_allow_price_edit"  # عدّل XML ID إذا مختلف
        )
        for order in self:
            order.allow_price_edit_user = bool(has_group)

    manual_price_edit = fields.Boolean(
        string="Manual Price Edit",
        default=True,
    )
    hide_button = fields.Boolean(
        string="Hide button",
        default=False,
    )

    def action_update_prices(self):
        self.manual_price_edit = False

        self.ensure_one()

        self._recompute_prices()

        if self.pricelist_id:

            message = _("Product prices have been recomputed according to pricelist %s.",
                        self.pricelist_id._get_html_link())
        else:
            message = _("Product prices have been recomputed.")
        self.message_post(body=message)
        self.manual_price_edit = True

    def write(self, vals):
        # خزّن الـ pricelist الحالية قبل الكتابة لتعرف فعليًا مين تغيّر
        prev_pl = {}
        if 'pricelist_id' in vals:
            for order in self:
                prev_pl[order.id] = order.pricelist_id.id or False

        res = super().write(vals)

        # إذا تغيّر الـ pricelist فعلاً على أي أمر، شغّل التحديث فورًا
        if 'pricelist_id' in vals:
            for order in self:
                new_pl = order.pricelist_id.id or False
                if prev_pl.get(order.id) != new_pl:
                    # لو حابب ما تحدّث لما ينمسح الـ pricelist (يصير False) ابقِ هذا الشرط
                    if new_pl:
                        order.with_context(from_update_prices=True).action_update_prices()
                    # لو بدك التحديث حتى عند التفريغ، احذف الشرط أعلاه واستدعِ الدالة على كل تغيير

        return res


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    allow_price_edit_user = fields.Boolean(
        string="Allow Price Edit (by current user)",
        compute="_compute_allow_price_edit_user_line",
        compute_sudo=False,
        store=False,
        help="Mirrors the permission of the current user (from the parent SO)."
    )
    manual_price_edit = fields.Boolean(
        related='order_id.manual_price_edit',
        string="Manual Price Edit",
    )
    hide_button = fields.Boolean(
        related='order_id.hide_button',
        string="Hide button",
    )

    @api.depends('order_id')
    @api.depends_context('uid')
    def _compute_allow_price_edit_user_line(self):
        # تحقّق المجموعة مرة واحدة للمستخدم الحالي
        has_group = self.env.user.has_group(
            "imc_sale_pricelist_edit.group_allow_price_edit"
        )
        for line in self:
            # لو في أمر بيع مرتبط، خذ قيمته؛ وإلا استخدم نتيجة مجموعة المستخدم مباشرة
            line.allow_price_edit_user = bool(
                line.order_id.allow_price_edit_user if line.order_id else has_group
            )

    def write(self, vals):
        res = super().write(vals)

        if "price_unit" in vals and self.manual_price_edit:
            for line in self:
                # Check if user has permission to edit price
                if line.allow_price_edit_user and line.order_id:
                    # Clear pricelist_id when manual price is edited
                    if line.order_id.state in ("draft","parent"):
                        line.order_id.write({"pricelist_id": False})

        return res
