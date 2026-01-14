from odoo import api, models,fields, _
from odoo.exceptions import UserError

class StockMove(models.Model):
    _inherit = 'stock.move'

    # يقرأ وصف سطر البيع مباشرة
    description_so = fields.Text(
        string="SO Description",
        related="sale_line_id.name",
        store=True,        # يخزّن القيمة لتسريع البحث/التجميع
        readonly=True,     # اجعله للعرض فقط (أزلها لو بدك الكتابة ترجع لسطر البيع)
        copy=False,
    )

class ReportDeliverySlipGuard(models.AbstractModel):
    # ملاحظة: نستخدم _name وليس _inherit
    # الاسم لازم يطابق Template Name في التقرير: stock.report_deliveryslip
    _name = 'report.stock.report_deliveryslip'
    _description = 'Delivery Slip report with done-state guard'

    @api.model
    def _get_report_values(self, docids, data=None):
        pickings = self.env['stock.picking'].browse(docids).exists()
        not_done = pickings.filtered(lambda p: p.state != 'done')
        if not_done:
            names = ", ".join(not_done.mapped('name'))
            raise UserError(_(
                "You can only print the Delivery Slip when the transfer is in Done state.\n"
                "Not done: %s"
            ) % names)
        # القيمة القياسية التي تتوقعها قوالب QWeb
        return {
            'doc_ids': pickings.ids,
            'doc_model': 'stock.picking',
            'docs': pickings,
        }

