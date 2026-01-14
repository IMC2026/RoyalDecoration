# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from markupsafe import Markup  # ✅ Add this import

class DuplicateConfirmWizard(models.TransientModel):
    _name = 'duplicate.confirm.wizard'
    _description = 'Confirm duplication for active_ids'

    message = fields.Html(
        readonly=True,
        sanitize=False,
        default=lambda self: Markup(
            '<span style="white-space:nowrap; font-weight:bold;">'
            'Are you sure you want to duplicate the selected record(s)?'
            '</span>'
        ),
    )

    def action_duplicate(self):
        self.ensure_one()
        model = self.env.context.get('active_model')
        ids = self.env.context.get('active_ids', [])
        if not model or not ids:
            return {'type': 'ir.actions.act_window_close'}

        records = self.env[model].browse(ids)
        for rec in records:
            rec.copy()

        return {'type': 'ir.actions.act_window_close'}

    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}
