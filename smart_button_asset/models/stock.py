from odoo import models, fields, api

from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    asset_count = fields.Integer(string="Assets Count", compute="_compute_asset_count")

    def _compute_asset_count(self):
        for move in self:
            move.asset_count = len(move.asset_ids)

    def action_open_assets(self):
        self.ensure_one()
        return {
            'name': 'Assets',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'account.asset.asset',
            'domain': [('id', 'in', self.asset_ids.ids)],
            'context': {'default_move_id': self.id},
        }

