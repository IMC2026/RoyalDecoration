from odoo import models, fields, api

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    line_no = fields.Integer(string="Line No.", compute="_compute_line_no", store=True)

    @api.depends('order_id.order_line.sequence', 'order_id.order_line.display_type')
    def _compute_line_no(self):
        for order in self.mapped('order_id'):
            # Filter out section and note lines
            non_section_lines = order.order_line.filtered(
                lambda line: line.display_type not in ('line_section', 'line_note')
            )
            # Sort by sequence (so it reflects drag-and-drop order)
            sorted_lines = non_section_lines.sorted(key=lambda l: l.sequence)
            for index, line in enumerate(sorted_lines, start=1):
                line.line_no = index

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # من ضغط Confirm (أرسل الطلب للاعتماد)
    confirm_requested_by_id = fields.Many2one(
        'res.users', string='Submitted by', readonly=True, copy=False
    )

    def button_confirm(self):
        # خزّن المستخدم الذي ضغط Confirm
        for po in self:
            po.confirm_requested_by_id = self.env.user
        # أكمل السلوك الافتراضي
        return super(PurchaseOrder, self).button_confirm()

    def write(self, vals):
        # احفظ الحالة قبل التغيير
        previous_states = {po.id: po.state for po in self}

        res = super(PurchaseOrder, self).write(vals)

        for po in self:
            previous_state = previous_states.get(po.id)
            new_state = po.state

            # 1) عند التحول إلى "to approve" أخبر المدراء (كما كان سابقاً)
            if new_state == 'to approve' and previous_state != 'to approve':
                group_admin = self.env.ref('purchase.group_purchase_manager', raise_if_not_found=False)
                if group_admin:
                    for user in group_admin.users:
                        # (اختياري) لا ترسل لمن ضغط Confirm بنفسه
                        if user.id == (po.confirm_requested_by_id.id or self.env.user.id):
                            continue
                        self.env['mail.activity'].create({
                            'res_model_id': self.env['ir.model']._get_id('purchase.order'),
                            'res_id': po.id,
                            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                            'summary': 'Approval Required',
                            'note': 'Please review and approve this Purchase Order.',
                            'user_id': user.id,
                        })

            # 2) من "to approve" إلى "purchase" — أرسل Activity فقط لمن ضغط Confirm
            elif previous_state == 'to approve' and new_state == 'purchase':
                target_user = po.confirm_requested_by_id or po.create_uid
                if target_user:
                    self.env['mail.activity'].create({
                        'res_model_id': self.env['ir.model']._get_id('purchase.order'),
                        'res_id': po.id,
                        'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                        'summary': 'Purchase Order Confirmed',
                        'note': 'Your Purchase Order has been approved and confirmed.',
                        'user_id': target_user.id,
                    })

        return res