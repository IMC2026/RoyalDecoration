from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        for order in self:
            partner = order.partner_id

            # Check for required fields
            missing_fields = []
            if not partner.name:
                missing_fields.append('Name')
            if not partner.arabic_name:
                missing_fields.append('Arabic Name')
            if not partner.street:
                missing_fields.append('Street')
            if not partner.city:
                missing_fields.append('City')
            if not partner.state_id:
                missing_fields.append('State')
            if not partner.zip:
                missing_fields.append('ZIP')
            if not partner.country_id:
                missing_fields.append('Country')
            if not partner.vat:
                missing_fields.append('VAT')
            if not partner.commercial_register_no:
                missing_fields.append('Commercial Register No')
            if not partner.phone:
                missing_fields.append('Phone')
            # if not partner.partner_attachment_ids.name:
            #     missing_fields.append('Attachment')

            if not partner.partner_attachment_ids:
                missing_fields.append('Attachment')

            if missing_fields:
                raise UserError(
                    f"You cannot confirm the Sale Order because the following partner fields are missing:\n- " +
                    "\n- ".join(missing_fields)
                )

        return super(SaleOrder, self).action_confirm()

    crm_lead_id_number = fields.Integer(
        string="CRM Lead ID",
        related="opportunity_id.id",
        store=True,
        index=True,
        readonly=True,
    )

class PartnerAttachment(models.Model):
    _name = 'partner.attachment'
    _description = 'Partner Attachment'

    name = fields.Char(string='File Name', required=True)
    attachment = fields.Many2many(
        'ir.attachment',
        'partner_attachment_ir_attachment_rel',
        'partner_attachment_id',
        'attachment_id',
        string="Files",
        required=True,
        help="Attach multiple files to this record."
    )
    partner_id = fields.Many2one('res.partner', string='Partner', ondelete='cascade')

    @api.model
    def create(self, vals):
        record = super(PartnerAttachment, self).create(vals)
        if 'attachment' in vals and record.attachment:
            record.attachment.write({
                'res_model': 'partner.attachment',
                'res_id': record.id,
            })
        return record

    def write(self, vals):
        res = super(PartnerAttachment, self).write(vals)
        if 'attachment' in vals:
            for record in self:
                if record.attachment:
                    record.attachment.write({
                        'res_model': 'partner.attachment',
                        'res_id': record.id,
                    })
        return res

class ResPartner(models.Model):
    _inherit = 'res.partner'

    partner_attachment_ids = fields.One2many(
        'partner.attachment',
        'partner_id',
        string='Attachments',
    )

    # def _check_required_attachments(self):
    #     for partner in self:
    #         if not partner.partner_attachment_ids:
    #             raise ValidationError("At least one attachment is required for the partner.")
    #
    #
    #
    # @api.model
    # def create(self, vals):
    #     partner = super(ResPartner, self).create(vals)
    #     self._check_required_attachments()
    #     return partner
    #
    # def write(self, vals):
    #     res = super(ResPartner, self).write(vals)
    #     self._check_required_attachments()
    #     return res


