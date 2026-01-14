from odoo import models, fields,api
from odoo.exceptions import UserError

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    line_no = fields.Integer(string="Line No.", store=True ,compute='_compute_line_no')

    # index = fields.Integer(string='Index', compute='_compute_index')

    # @api.depends('order_id.order_line')
    @api.depends('move_id.invoice_line_ids')
    def _compute_line_no(self):
        for move in self.mapped('move_id'):
            non_section_lines = move.invoice_line_ids.filtered(
                lambda line: line.display_type not in ('line_section', 'line_note'))
            for index, line in enumerate(non_section_lines, start=1):
                line.line_no = index

    # @api.depends('move_id.line_ids', 'move_id.line_ids.sequence')
    # def _compute_line_no(self):
    #     for move in self.mapped('move_id'):
    #         # Exclude Section and Note lines and sort consistently
    #         valid_lines = move.line_ids.filtered(
    #             lambda l: l.display_type not in ['line_section', 'line_note']
    #         ).sorted(key=lambda l: l.sequence or l.id)
    #
    #         for index, line in enumerate(valid_lines, start=1):
    #             line.line_no = index
    #
    #         # Set line_no to 0 for excluded lines (optional but recommended)
    #         excluded_lines = move.line_ids.filtered(
    #             lambda l: l.display_type in ['line_section', 'line_note']
    #         )
    #         excluded_lines.line_no = 0

    # def unlink(self):
    #     move_ids = self.mapped('move_id')  # Store related move_ids before deletion
    #     res = super(AccountMoveLine, self).unlink()  # Delete the records
    #     for move in move_ids:
    #         move.line_ids._compute_line_no()  # Recompute line numbers for remaining lines
    #     return res
class ResCurrency(models.Model):
    _inherit = 'res.currency'

    # def write(self, vals):
    #     if 'rounding' in vals:
    #         rounding_val = vals['rounding']
    #         for record in self:
    #             if (rounding_val > record.rounding or rounding_val == 0) and record._has_accounting_entries():
    #                 pass
    #                 raise UserError("You cannot reduce the number of decimal places of a currency which has already been used to make accounting entries.")
    #
    #     return super(ResCurrency, self).write(vals)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    account_name = fields.Char(string="Account Name")
    arabic_name = fields.Char(string="Arabic Name", placeholder="الإسم بالعربي")
    iban = fields.Char(string="IBAN")
    bank_name = fields.Char(string="Bank Name")
    city_name = fields.Char(string="City")

    commercial_register_no = fields.Char(
        string='Commercial Register No',
        index=True,
        help="The commercial register number. Values will be validated based on the country format. "
             "Use '/' to indicate that the partner is not subject to tax."
    )
class ResCompany(models.Model):
    _inherit = 'res.company'

    bank_account_name = fields.Char(string="Account Name")
    arabic_name = fields.Char(string="Arabic Name", placeholder="الإسم بالعربي")
    bank_iban = fields.Char(string="IBAN")
    bank_name = fields.Char(string="Bank Name")
    bank_city = fields.Char(string="City")
    logo2 = fields.Binary(string="Secondary Logo")
    # logo4 = fields.Binary(string="Additional Logo")

    commercial_register_no = fields.Char(
        string='Commercial Register No',
        index=True,
        help="The commercial register number. Values will be validated based on the country format. "
             "Use '/' to indicate that the partner is not subject to tax."
    )