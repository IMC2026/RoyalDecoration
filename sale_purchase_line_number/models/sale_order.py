from odoo import models, fields, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    line_no = fields.Integer(string="Line No.", compute="_compute_line_no", store=True)

    # @api.depends('order_id.order_line')
    # def _compute_line_no(self):
    #     for order in self.mapped('order_id'):
    #         non_section_lines = order.order_line.filtered(
    #             lambda line: line.display_type not in ('line_section', 'line_note'))
    #         for index, line in enumerate(non_section_lines, start=1):
    #             line.line_no = index

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
