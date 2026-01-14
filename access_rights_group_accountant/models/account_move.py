from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = "account.move"

    @api.depends('restrict_mode_hash_table', 'state')
    def _compute_show_reset_to_draft_button(self):
        print("this is the override function of _compute_show_reset_to_draft_button")
        accountant_group = self.env.user.has_group('account.group_account_user' )
        for move in self:
            if self.env.user.has_group('account.group_account_manager'):
                move.show_reset_to_draft_button = (
                        not move.restrict_mode_hash_table
                        and move.state in ('posted', 'cancel')

                )
            else :
                move.show_reset_to_draft_button = (
                    not move.restrict_mode_hash_table
                    and move.state in ('posted', 'cancel')
                    and not accountant_group  # Hide for accountants
                )
