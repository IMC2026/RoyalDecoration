# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from odoo.exceptions import AccessError



class SaleOrder(models.Model):
    _inherit = 'sale.order'

    version_no = fields.Integer(string="Version Number", copy=False, default=0)
    sale_order_origin_version = fields.Many2one('sale.order', copy=False, string="Origin Sales Order")
    show_ready_to_sent = fields.Boolean(default=True, copy=False)
    is_final_version = fields.Boolean(string="Final Version", default=False, copy=False)

    so_revisions_count = fields.Integer(string="Sale Order Revisions Count", compute='_get_so_revisions')
    so_origin_count = fields.Integer(string="Sale Order Origins Count", compute='_get_so_origins')

    show_confirm_button = fields.Boolean(
        string="Show Confirm Button",
        compute="_compute_show_confirm_button",
        store=False
    )

    state = fields.Selection(
        selection_add=[('parent', 'Parent')],
        ondelete={'parent': 'set default'},
    )

    def action_open_delivery_wizard(self):
        return super(SaleOrder, self.with_context(
            carrier_recompute=True,
           )).action_open_delivery_wizard()

    @api.constrains('state')
    def _check_only_one_active_revision(self):
        """Ensure only one active (non-cancel) revision per origin."""
        for order in self:
            if order.sale_order_origin_version and order.state != 'cancel':
                active_revisions = self.search([
                    ('sale_order_origin_version', '=', order.sale_order_origin_version.id),
                    ('state', '!=', 'cancel'),
                    ('id', '!=', order.id),
                ])
                if active_revisions:
                    raise ValidationError(_(
                        "There can only be one active revision at a time. "
                        "Please cancel other revisions before activating this one."
                    ))

    @api.depends("so_origin_count", "so_revisions_count")
    def _compute_show_confirm_button(self):
        for order in self:
            order.show_confirm_button = (
                order.state == 'draft'
                and order.so_origin_count >= 0
                and order.so_revisions_count == 0
            )

     # 1) action_update_prices: call create_so_version(open_form=False) and stay put
    def action_update_prices(self):
        """Update prices and create new version only if prices actually changed"""
        print("=== action_update_prices STARTED ===")

        # Store original prices before update
        original_prices = {}
        for order in self:
            if (order.is_final_version
                    and not order.sale_order_origin_version
                    and order.state in ('draft', 'sent', 'parent')):
                original_prices[order.id] = {line.id: line.price_unit for line in order.order_line}
                print(f"Stored prices for order {order.name}")

        # Call the original method to update prices WITH CONTEXT
        result = super(SaleOrder, self.with_context(from_price_update=True)).action_update_prices()
        print("Super method called")

        # Check if prices actually changed and create new version if needed
        version_created = False
        for order in self:
            if (order.is_final_version
                    and not order.sale_order_origin_version
                    and order.state in ('draft', 'sent', 'parent')
                    and order.id in original_prices):

                prices_changed = False
                changed_lines = []
                for line in order.order_line:
                    original_price = original_prices[order.id].get(line.id)
                    if original_price is not None and line.price_unit != original_price:
                        prices_changed = True
                        changed_lines.append(f"Line {line.id}: {original_price} → {line.price_unit}")
                        break

                print(f"Order {order.name} - Prices changed: {prices_changed}")
                if changed_lines:
                    print("Changed lines:", changed_lines)

                if prices_changed and not version_created:
                    print("Creating new version (without navigating)...")
                    version_created = True
                    # Prevent write-trigger path from creating another version, and do NOT open the new form
                    order.with_context(skip_revision_create=True).create_so_version(open_form=False)

                    # Option A (recommended): reload current form so you see the updated state immediately
                    # return {
                    #     "type": "ir.actions.client",
                    #     "tag": "reload",
                    # }

                    # Option B: if you prefer to avoid reloads, just break and fall through to `result`
                    break

        print("=== action_update_prices COMPLETED ===")
        return result

    def action_draft(self):
        # origins that were cancel before reopening
        origins_were_cancel = self.filtered(
            lambda o: not o.sale_order_origin_version and o.state == 'cancel'
        )

        # For revisions: cancel all other revisions when setting one to draft
        revisions_to_draft = self.filtered(lambda o: o.sale_order_origin_version)
        if revisions_to_draft:
            origin_id = revisions_to_draft.sale_order_origin_version.id
            other_revisions = self.search([
                ('sale_order_origin_version', '=', origin_id),
                ('state', '!=', 'cancel'),
                ('id', 'not in', revisions_to_draft.ids),
            ])
            if other_revisions:
                other_revisions.with_context(allow_revision_cancel=True).action_cancel()

        res = super().action_draft()

        # Reopen canceled revisions of reopened origins
        if origins_were_cancel:
            revisions_to_reopen = self.search([
                ('sale_order_origin_version', 'in', origins_were_cancel.ids),
                ('state', '=', 'cancel'),
            ])
            if revisions_to_reopen:
                revisions_to_reopen.with_context(allow_revision_write=True).action_draft()

        return res

    def action_confirm(self):
        """Allow confirming child revisions by bypassing revision write guard
        and canceling sibling revisions first to satisfy the single-active rule.
        """
        # Split: children (revisions) vs origins
        children = self.filtered(lambda o: o.sale_order_origin_version)
        origins = self - children

        # For each child, cancel other non-cancel siblings BEFORE confirm (avoid constraint)
        for child in children:
            siblings = self.search([
                ('sale_order_origin_version', '=', child.sale_order_origin_version.id),
                ('id', '!=', child.id),
                ('state', '!=', 'cancel'),
            ])
            if siblings:
                siblings.with_context(allow_revision_cancel=True, allow_revision_write=True).action_cancel()

        # Call super with context that allows writes during confirm on revisions
        self_ctx = self.with_context(
            skip_revision_create=True,
            allow_revision_write=True,  # <-- bypass _check_revision_context
            action='action_confirm',  # <-- your guard already whitelists this
            allow_parent_edit_when_child_sale=True,
        )
        res = super(SaleOrder, self_ctx).action_confirm()

        # Keep your original behavior for origins that became 'sale': cancel their revisions
        confirmed_origins = origins.filtered(lambda o: o.state == 'sale')
        if confirmed_origins:
            revisions = self.search([
                ('sale_order_origin_version', 'in', confirmed_origins.ids),
                ('state', '!=', 'cancel'),
            ])
            if revisions:
                revisions.with_context(allow_revision_cancel=True).action_cancel()

        return res

    # def action_confirm(self):
    #     if not self.env.user.has_group("sale_order_create_version.group_sale_confirm_button"):
    #         raise AccessError(_("You are not allowed to confirm Sales Orders."))
    #     return super().action_confirm()


    # 2) create_so_version: add open_form flag (default True to preserve old behavior)
    def create_so_version(self, open_form=True):
        self.ensure_one()

        child_in_sale = self.search([
            ('sale_order_origin_version', '=', self.id),
            ('state', '=', 'sale'),
        ], limit=1)
        if child_in_sale:
            raise UserError(_("Cannot create new version when a child revision is in 'sale' state."))

        # Hide button on current record and mark as parent
        self.write({
            'show_ready_to_sent': False,
            'is_final_version': True,
            'state': 'parent',
        })

        # Cancel existing revisions
        existing_revisions = self.search([
            ('sale_order_origin_version', '=', self.id),
            ('state', '!=', 'cancel'),
        ])
        if existing_revisions:
            existing_revisions.with_context(allow_revision_cancel=True).action_cancel()

        # Build new name with next suffix
        base_name = self.name.split('-')[0] if '-' in self.name else self.name
        versions = self.search([
            '|',
            ('id', '=', self.id),
            ('sale_order_origin_version', '=', self.id),
        ])

        suffixes = []
        for v in versions:
            if '-' in v.name:
                suffix_part = v.name.split('-')[-1]
                if suffix_part.isdigit():
                    suffixes.append(int(suffix_part))

        next_revision = 0 if not suffixes else max(suffixes) + 1
        new_name = f"{base_name}-{next_revision:02d}"

        new_order = self.copy({
            'name': new_name,
            'state': 'draft',
            'sale_order_origin_version': self.id,
            'version_no': next_revision,
            'show_ready_to_sent': False,
            'is_final_version': True,
        })

        # If caller wants to stay on the same screen, do not return a navigation action
        if not open_form:
            return new_order

        return {
            'type': 'ir.actions.act_window',
            'name': new_order.name,
            'res_model': 'sale.order',
            'view_mode': 'form',
            'view_id': self.env.ref('sale.view_order_form').id,
            'target': 'current',
            'res_id': new_order.id,
            'context': {
                'from_revision_view': True,
                'from_version_create': True,
            },
        }

    def _get_so_revisions(self):
        for order in self:
            order.so_revisions_count = self.search_count([
                ('sale_order_origin_version', '=', order.id)
            ])

    def _get_so_origins(self):
        for order in self:
            order.so_origin_count = 1 if order.sale_order_origin_version else 0

    def action_view_sale_revisions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Revisions'),
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'domain': [('sale_order_origin_version', '=', self.id)],
            'context': {'from_revision_view': True},
        }

    def action_view_sale_origin(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Origin Order'),
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': self.sale_order_origin_version.id,
            'context': {'from_revision_view': False},
        }

    def _check_revision_context(self, vals=None):
        """
        Prevent edits on revisions unless explicitly allowed in context.
        Also lock parent when any child is in 'sale' (unless explicitly bypassed).
        """
        allowed_when_revision = {
            'state', 'access_token',
            'signature', 'signed_by', 'signed_on', 'is_expired',
        }
        # What a parent may still change while a child is in 'sale'
        safe_fields_parent_when_child_sale = {
            'state', 'access_token', 'note', 'description',
            # add any other harmless fields you want to allow on the parent:
            'client_order_ref', 'validity_date',
        }

        # Global bypass (admin/explicit flows)
        if self.env.context.get('allow_revision_write'):
            return

        # Let explicit action contexts pass (e.g., child action_confirm)
        if self.env.context.get('action') in ['action_confirm']:
            return

        for order in self:
            # ----- CHILD (revision) GUARD -----
            if order.sale_order_origin_version:
                if self.env.context.get('action_open_discount_wizard') or 'discount' in (vals or {}):
                    raise UserError(_("Cannot open discount wizard in revision mode."))

                changed = set((vals or {}).keys())
                disallowed = [f for f in changed if f not in allowed_when_revision]
                if disallowed:
                    raise UserError(_("You cannot modify this revision except for allowed State field."))

            # ----- PARENT GUARD (when any child is in 'sale') -----
            else:
                if order.state == 'parent':
                    child_in_sale = self.search([
                        ('sale_order_origin_version', '=', order.id),
                        ('state', '=', 'sale'),
                    ], limit=1)

                    if child_in_sale and not self.env.context.get('allow_parent_edit_when_child_sale'):
                        changed = set((vals or {}).keys())
                        disallowed = [f for f in changed if f not in safe_fields_parent_when_child_sale]
                        if disallowed:
                            raise UserError(_("Cannot edit the parent order while a child revision is in 'sale'. "))

    def write(self, vals):
        self._check_revision_context(vals)


        for order in self:
            # Only for parent orders
            if not order.sale_order_origin_version:
                # Is any child in 'sale'?
                child_in_sale = bool(self.search([
                    ('sale_order_origin_version', '=', order.id),
                    ('state', '=', 'sale')
                ], limit=1))

                # Move origin order to 'parent' if conditions met, create new revision
                if (
                    order.is_final_version
                    and order.state in ('draft', 'sent', 'parent')
                        and not (
                        self.env.context.get('skip_revision_create')
                        or self.env.context.get('carrier_recompute')  # <— أضِف هذا
                )

                    and not set(vals.keys()).issubset({'has_message','pricelist_id','message_is_follower','message_partner_ids','access_url','show_update_pricelist','manual_price_edit','id','state','date_order', 'access_token','applied_coupon_ids'})


                        and not child_in_sale
                ):
                    if order.state != 'parent':
                        super(SaleOrder, order).write({'state': 'parent'})

                    super(SaleOrder, order).write(vals)

                    # Cancel existing (non-cancel) revisions
                    existing_revisions = self.search([
                        ('sale_order_origin_version', '=', order.id),
                        ('state', '!=', 'cancel')
                    ])
                    if existing_revisions:
                        existing_revisions.with_context(allow_revision_cancel=True).action_cancel()

                    # Compute next suffix
                    base_name = order.name.split('-')[0] if '-' in order.name else order.name
                    versions = self.search([
                        '|',
                        ('id', '=', order.id),
                        ('sale_order_origin_version', '=', order.id)
                    ])
                    suffixes = []
                    for v in versions:
                        if '-' in v.name:
                            suffix_part = v.name.split('-')[-1]
                            if suffix_part.isdigit():
                                suffixes.append(int(suffix_part))
                    next_revision = max(suffixes) + 1 if suffixes else 1
                    new_name = f"{base_name}-{next_revision:02d}"

                    new_order = order.copy({
                        'name': new_name,
                        'state': 'draft',
                        'sale_order_origin_version': order.id,
                        'version_no': next_revision,
                        'show_ready_to_sent': False,
                        'is_final_version': True,
                    })

                    return {
                        'type': 'ir.actions.act_window',
                        'name': new_order.name,
                        'res_model': 'sale.order',
                        'view_mode': 'form',
                        'res_id': new_order.id,
                        'view_id': self.env.ref('sale.view_order_form').id,
                        'target': 'current',
                        'context': {'from_revision_view': True},
                    }

        return super().write(vals)

    def unlink(self):
        self._check_revision_context()
        return super().unlink()

    def copy(self, default=None):
        self._check_revision_context()
        return super().copy(default)

    def action_quotation_send(self):
        for order in self:
            if order.so_revisions_count >= 0 and not order.sale_order_origin_version:
                if order.state != 'sale':
                    raise ValidationError(
                        _("You cannot send 'PRO-FORMA Invoice' or 'Send by Email' on the Origin version of the order. Please open a Revision to proceed.")
                    )
                else:
                    return super(SaleOrder, self).action_quotation_send()

            elif order.so_origin_count >= 1 and order.sale_order_origin_version:
                return super(SaleOrder, self).action_quotation_send()

        return super().action_quotation_send()

    def _action_send_safe(self):
        return super(SaleOrder, self).action_quotation_send()



class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        self._check_sale_report_block(report_ref, res_ids)
        return super()._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)

    def _check_sale_report_block(self, report_ref, res_ids):
        if report_ref in ['sale.report_saleorder', 'sale.report_saleorder_raw']:
            orders = self.env['sale.order'].browse(res_ids)
            for order in orders:
                if order.so_revisions_count >= 0 and not order.sale_order_origin_version and order.state in ('draft', 'sent','parent'):
                    raise UserError(
                        _("You cannot print this report while this order has revisions. Please use the Revisions view."))

class SaleOrderDiscount(models.TransientModel):
    _inherit = 'sale.order.discount'

    def action_apply_discount(self):
        ctx = self.env.context
        orders = self.env['sale.order'].browse(
            ctx.get('active_ids') or ([ctx['active_id']] if ctx.get('active_id') else [])
        )
        if not orders and 'order_id' in self._fields:
            orders = self.mapped('order_id')

        # Block on revisions (children)
        for order in orders:
            if order.sale_order_origin_version:
                raise UserError(_("You cannot apply a discount on a Sales Order *Revision*. Open the origin order."))

        # Block on parent while any child is in 'sale' (unless bypassed via context)
        if not ctx.get('allow_parent_edit_when_child_sale'):
            parents = orders.filtered(lambda o: not o.sale_order_origin_version and o.state == 'parent')
            if parents:
                any_child_in_sale = bool(self.env['sale.order'].search_count([
                    ('sale_order_origin_version', 'in', parents.ids),
                    ('state', '=', 'sale'),
                ]))
                if any_child_in_sale:
                    raise UserError(_(
                        "You cannot apply a discount on the *Parent* order while a child revision is in 'sale'. "
                        "Open the active child revision instead."
                    ))

        return super().action_apply_discount()


class SaleLoyaltyCouponWizard(models.TransientModel):
    _inherit = 'sale.loyalty.coupon.wizard'

    def action_apply(self):
        self.ensure_one()
        ctx = self.env.context

        order = self.order_id or self.env['sale.order'].browse(ctx.get('active_id'))
        if not order:
            raise UserError(_("Invalid sales order."))

        # Block on revisions (children)
        if order.sale_order_origin_version:
            raise UserError(_("You cannot apply a discount on a Sales Order *Revision*. Open the origin order."))

        # Block on parent while any child is in 'sale' (unless bypassed via context)
        if not ctx.get('allow_parent_edit_when_child_sale'):
            if not order.sale_order_origin_version and order.state == 'parent':
                child_in_sale = bool(self.env['sale.order'].search_count([
                    ('sale_order_origin_version', '=', order.id),
                    ('state', '=', 'sale'),
                ]))
                if child_in_sale:
                    raise UserError(_(
                        "You cannot apply a discount on the *Parent* order while a child revision is in 'sale'. "
                        "Open the active child revision instead."
                    ))

        return super().action_apply()
