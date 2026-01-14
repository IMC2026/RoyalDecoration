# models/stock_picking_type.py  (أو ضعها في models/stock_picking.py إن أحببت)
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'
    is_consignment = fields.Boolean(string="Is Consignment")


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # مفيدة لشرط الإظهار في العرض
    is_consignment = fields.Boolean(related='picking_type_id.is_consignment', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        """
        يمنع إنشاء consignment بدون Owner.
        هذا يتحقق قبل الحفظ، لذلك لا يتم استهلاك أي رقم تسلسل مطلقًا.
        """
        for vals in vals_list:
            picking_type_id = vals.get('picking_type_id') or self.env.context.get('default_picking_type_id')
            if picking_type_id:
                ptype = self.env['stock.picking.type'].browse(picking_type_id)
                if ptype.is_consignment and not vals.get('owner_id'):
                    raise UserError(_(
                        "Assign Owner is required for Consignment.\n"
                        "If the Assign Owner field is hidden, go to Settings and enable Consignment."
                    ))
        return super().create(vals_list)

    def write(self, vals):
        """
        حارس إضافي: يمنع التحويل إلى Consignment أو إزالة الـ Owner
        على سجل Consignment موجود.
        """
        for rec in self:
            new_type = self.env['stock.picking.type'].browse(vals['picking_type_id']) if 'picking_type_id' in vals else rec.picking_type_id
            new_owner_id = vals.get('owner_id', rec.owner_id.id)
            if new_type.is_consignment and not new_owner_id:
                raise UserError(_(
                    "Assign Owner is required for Consignment.\n"
                    "If the Assign Owner field is hidden, go to Settings and enable Consignment."
                ))
        return super().write(vals)

    def button_validate(self):
        # حارس نهائي في وقت التحقق
        for picking in self:
            if picking.picking_type_id.is_consignment and not picking.owner_id:
                raise UserError(_(
                    "Assign Owner is required for Consignment.\n"
                    "If the Assign Owner field is hidden, go to Settings and enable Consignment."
                ))
        return super().button_validate()
