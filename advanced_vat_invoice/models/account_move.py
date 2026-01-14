# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import base64
from io import BytesIO
import qrcode
import pytz
from odoo.tools import str2bool


class AccountMove(models.Model):
    _inherit = 'account.move'

    # Binary field to hold the generated QR image
    qr = fields.Binary("QR Code", readonly=True, copy=False, attachment=True)
    # UI helpers (show/hide button/section)
    qr_button = fields.Boolean(compute="_compute_qr", string="Show Generate QR Button")
    qr_page = fields.Boolean(compute="_compute_qr", string="Show QR Page/Tab")

    @api.depends('state')
    def _compute_qr(self):
        """Control visibility of the QR button/section from settings + move state."""
        params = self.env['ir.config_parameter'].sudo()
        is_qr = params.get_param('advanced_vat_invoice.is_qr')
        mode = params.get_param('advanced_vat_invoice.generate_qr')
        for record in self:
            # Button only in manual mode and when QR feature is enabled
            record.qr_button = bool(is_qr) and mode == 'manually'
            # Page visible if feature enabled AND (manual with posted/cancelled OR automatic)
            record.qr_page = bool(is_qr) and (
                (mode == 'manually' and record.state in ['posted', 'cancelled']) or
                (mode == 'automatically')
            )

    def action_post(self):
        res = super().action_post()
        params = self.env['ir.config_parameter'].sudo()
        mode = params.get_param('advanced_vat_invoice.generate_qr') or 'manually'
        is_qr = str2bool(params.get_param('advanced_vat_invoice.is_qr', 'False'))
        if is_qr and mode == 'automatically':
            self.generate_qrcode()  # سيملأ الحقل qr للفواتير التي أصبحت Posted
        return res

    @api.depends(
        'state',
        'company_id.name', 'company_id.vat',
        'amount_total', 'amount_tax',
        'currency_id', 'invoice_date'
    )
    def generate_qrcode(self):
        """Generate and store QR image automatically (if settings allow)."""
        params = self.env['ir.config_parameter'].sudo()
        mode = params.get_param('advanced_vat_invoice.generate_qr')

        if not (qrcode and base64):
            raise UserError(_('Necessary Requirements To Run This Operation Is Not Satisfied'))

        for rec in self:
            if rec.state == 'posted' and mode == 'automatically':
                data = rec.qr_code_data()
                if not data:
                    rec.qr = False
                    continue
                qr = qrcode.QRCode(
                    version=4,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=4,
                    border=1,
                )
                qr.add_data(data)
                qr.make(fit=True)
                img = qr.make_image()
                buf = BytesIO()
                img.save(buf, format="PNG")
                rec.qr = base64.b64encode(buf.getvalue())
            else:
                # Do not alter existing QR in non-automatic modes here
                pass

    def generate_qr_button(self):
        """Manual generation from button; safe for multi-record sets."""
        params = self.env['ir.config_parameter'].sudo()
        mode = params.get_param('advanced_vat_invoice.generate_qr')

        if not (qrcode and base64):
            raise UserError(_('Necessary Requirements To Run This Operation Is Not Satisfied'))

        for rec in self:
            if mode != 'manually':
                # Respect the setting: only allow manual generation in manual mode
                continue
            data = rec.qr_code_data()
            if not data:
                continue
            qr = qrcode.QRCode(
                version=4,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=4,
                border=1,
            )
            qr.add_data(data)
            qr.make(fit=True)
            img = qr.make_image()
            buf = BytesIO()
            img.save(buf, format="PNG")
            rec.qr = base64.b64encode(buf.getvalue())

    # -------------------- Helpers for TLV / ZATCA-style QR --------------------

    def _tlv(self, tag_int, value_str):
        """Encode (tag, length, value) to hex per TLV, with UTF-8 bytes."""
        if value_str is None:
            value_str = ''
        value_bytes = value_str.encode('utf-8')
        tag_byte = bytes([int(tag_int)])
        length_byte = bytes([len(value_bytes)])
        return (tag_byte + length_byte + value_bytes).hex()

    def _tlv_base64(self, tlv_hex_concat):
        """Return base64 of the hex-encoded TLV bytes."""
        raw = bytes.fromhex(tlv_hex_concat)
        return base64.b64encode(raw).decode()

    def timezone(self, userdate):
        """Convert a datetime to the user's timezone string in ISO 8601 format."""
        # No ensure_one() needed; safe to use env.context / env.user across records.
        tz_name = (self.env.context.get('tz')
                   or getattr(self.env.user, 'tz', None)
                   or 'UTC')
        tz = pytz.timezone(tz_name)
        if userdate.tzinfo is None:
            # Make it timezone-aware in UTC first
            userdate = pytz.utc.localize(userdate)
        dt_local = userdate.astimezone(tz)
        return dt_local.strftime('%Y-%m-%dT%H:%M:%S%z')

    def qr_code_data(self):
        """Build the QR data payload (Base64 TLV with tags 1..5).
        Tags:
          1: Seller Name
          2: VAT Number
          3: Timestamp (ISO 8601 with offset)
          4: Total (with VAT)
          5: VAT Amount
        """
        self.ensure_one()

        # Seller details
        seller_name = (self.company_id.name or '').strip()
        seller_vat = (self.company_id.vat or '').strip()

        # Timestamp: use create_date if available, else now
        dt = self.create_date or fields.Datetime.now()
        timestamp = self.timezone(dt)

        # Amounts; convert to SAR if currency exists, otherwise keep as-is
        amount_total = self.amount_total or 0.0
        amount_tax = self.amount_tax or 0.0

        sar = self.env.ref('base.SAR', raise_if_not_found=False)
        company = self.env.company
        inv_date = self.invoice_date or fields.Date.today()

        if sar and self.currency_id and self.currency_id != sar:
            try:
                amount_total = self.currency_id._convert(amount_total, sar, company, inv_date)
                amount_tax = self.currency_id._convert(amount_tax, sar, company, inv_date)
            except Exception:
                # If conversion fails for any reason, keep original amounts
                pass

        # Format numbers to 2 decimals
        total_str = ('%.2f' % amount_total)
        tax_str = ('%.2f' % amount_tax)

        # Build TLV hex (dynamic lengths)
        tlv_hex = ''.join([
            self._tlv(1, seller_name),
            self._tlv(2, seller_vat),
            self._tlv(3, timestamp),
            self._tlv(4, total_str),
            self._tlv(5, tax_str),
        ])

        return self._tlv_base64(tlv_hex)


# تغيّر بالملف؟
# جعلنا التوليد per-record في الحالتين:
# الحقل المحسوب generate_qrcode (الوضع التلقائي).
#
# زر generate_qr_button (الوضع اليدوي).
#
# أضفنا self.ensure_one() داخل qr_code_data() لمنع أي singleton errors.
#
# حسّنّا منطق إظهار الأزرار/التبويب عبر _compute_qr باستخدام إعدادات:
#
# advanced_vat_invoice.is_qr
#
# advanced_vat_invoice.generate_qr (manually/automatically)
#
# دالة qr_code_data() تولّد TLV (وسيطرة على الأطوال ديناميكيًا) وترجع Base64، مع:
#
# اسم البائع (Tag 1)
#
# رقم ضريبة البائع (Tag 2)
#
# ختم الوقت (Tag 3) بـ ISO 8601 مع الأوفست من توقيت المستخدم
#
# الإجمالي شامل الضريبة (Tag 4)
#
# الضريبة (Tag 5)

# # -*- coding: utf-8 -*-
# ###############################################################################
# #
# #    Cybrosys Technologies Pvt. Ltd.
# #
# #    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
# #    Author: Gayathri V(odoo@cybrosys.com)
# #
# #    You can modify it under the terms of the GNU AFFERO
# #    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
# #
# #    This program is distributed in the hope that it will be useful,
# #    but WITHOUT ANY WARRANTY; without even the implied warranty of
# #    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# #    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
# #
# #    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
# #    (AGPL v3) along with this program.
# #    If not, see <http://www.gnu.org/licenses/>.
#
# ###############################################################################
# from io import BytesIO
# import binascii
# import pytz
#
# from odoo import api, fields, models, _
# from odoo.exceptions import UserError
# from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
#
# try:
#     import qrcode
# except ImportError:
#     qrcode = None
# try:
#     import base64
# except ImportError:
#     base64 = None
#
#
# class AccountMove(models.Model):
#     """Class for adding new button and a page in account move"""
#     _inherit = 'account.move'
#
#
#     qr = fields.Binary(string="QR Code", compute='generate_qrcode', store=True,
#                        help="QR code")
#     qr_button = fields.Boolean(string="Qr Button", compute="_compute_qr",
#                                help="Is QR button is enable or not")
#     qr_page = fields.Boolean(string="Qr Page", compute="_compute_qr",
#                              help="Is QR page is enable or not")
#
#     @api.depends('qr_button')
#     def _compute_qr(self):
#         """Compute function for checking the value of a field in settings"""
#         for record in self:
#             qr_code = self.env['ir.config_parameter'].sudo().get_param(
#                 'advanced_vat_invoice.is_qr')
#             qr_code_generate_method = self.env[
#                 'ir.config_parameter'].sudo().get_param(
#                 'advanced_vat_invoice.generate_qr')
#             record.qr_button = True if qr_code and qr_code_generate_method == 'manually' else False
#             record.qr_page = True if (qr_code and record.state in ['posted',
#                                                                    'cancelled']
#                                       and qr_code_generate_method == 'manually'
#                                       or qr_code_generate_method == 'automatically') \
#                 else False
#
#     def timezone(self, userdate):
#         """Function to convert a user's date to their timezone."""
#         tz_name = self.env.context.get('tz') or self.env.user.tz
#         contex_tz = pytz.timezone(tz_name)
#         date_time = pytz.utc.localize(userdate).astimezone(contex_tz)
#         return date_time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
#
#     def string_hexa(self, value):
#         """Convert a string to a hexadecimal representation."""
#         if value:
#             string = str(value)
#             string_bytes = string.encode("UTF-8")
#             encoded_hex_value = binascii.hexlify(string_bytes)
#             hex_value = encoded_hex_value.decode("UTF-8")
#             return hex_value
#
#     def hexa(self, tag, length, value):
#         """Generate a hex value with tag, length, and value."""
#         if tag and length and value:
#             hex_string = self.string_hexa(value)
#             length = int(len(hex_string) / 2)
#             conversion_table = ['0', '1', '2', '3', '4', '5', '6', '7', '8',
#                                 '9', 'a', 'b', 'c', 'd', 'e', 'f']
#             hexadecimal = ''
#             while (length > 0):
#                 remainder = length % 16
#                 hexadecimal = conversion_table[remainder] + hexadecimal
#                 length = length // 16
#             if len(hexadecimal) == 1:
#                 hexadecimal = "0" + hexadecimal
#             return tag + hexadecimal + hex_string
#
#     def qr_code_data(self):
#         """Generate QR code data for the current record."""
#         seller_name = str(self.company_id.name)
#         seller_vat_no = self.company_id.vat or ''
#         seller_hex = self.hexa("01", "0c", seller_name)
#         vat_hex = self.hexa("02", "0f", seller_vat_no) or ""
#         time_stamp = self.timezone(self.create_date)
#         date_hex = self.hexa("03", "14", time_stamp)
#         amount_total = self.currency_id._convert(
#             self.amount_total,
#             self.env.ref('base.SAR'),
#             self.env.company, self.invoice_date or fields.Date.today())
#         total_with_vat_hex = self.hexa("04", "0a",
#                                        str(round(amount_total, 2)))
#         amount_tax = self.currency_id._convert(
#             self.amount_tax,
#             self.env.ref('base.SAR'),
#             self.env.company, self.invoice_date or fields.Date.today())
#         total_vat_hex = self.hexa("05", "09",
#                                   str(round(amount_tax, 2)))
#         qr_hex = (seller_hex + vat_hex + date_hex + total_with_vat_hex +
#                   total_vat_hex)
#         encoded_base64_bytes = base64.b64encode(bytes.fromhex(qr_hex)).decode()
#         return encoded_base64_bytes
#
#     @api.depends('state')
#     def generate_qrcode(self):
#         """Generate and save QR code after the invoice is posted."""
#         param = self.env['ir.config_parameter'].sudo()
#         qr_code = param.get_param('advanced_vat_invoice.generate_qr')
#         for rec in self:
#             if rec.state == 'posted':
#                 if qrcode and base64:
#                     if qr_code == 'automatically':
#                         qr = qrcode.QRCode(
#                             version=4,
#                             error_correction=qrcode.constants.ERROR_CORRECT_L,
#                             box_size=4,
#                             border=1,
#                         )
#                         qr.add_data(self._origin.qr_code_data())
#                         qr.make(fit=True)
#                         img = qr.make_image()
#                         temp = BytesIO()
#                         img.save(temp, format="PNG")
#                         qr_image = base64.b64encode(temp.getvalue())
#                         rec.qr = qr_image
#                 else:
#                     raise UserError(
#                         _('Necessary Requirements To Run This Operation Is '
#                           'Not Satisfied'))
#
#     def generate_qr_button(self):
#         """Manually generate and save QR code."""
#         param = self.env['ir.config_parameter'].sudo()
#         qr_code = param.get_param('advanced_vat_invoice.generate_qr')
#         for rec in self:
#             if qrcode and base64:
#                 if qr_code == 'manually':
#                     qr = qrcode.QRCode(
#                         version=4,
#                         error_correction=qrcode.constants.ERROR_CORRECT_L,
#                         box_size=4,
#                         border=1,
#                     )
#                     qr.add_data(self.qr_code_data())
#                     qr.make(fit=True)
#                     img = qr.make_image()
#                     temp = BytesIO()
#                     img.save(temp, format="PNG")
#                     qr_image = base64.b64encode(temp.getvalue())
#                     rec.qr = qr_image
#             else:
#                 raise UserError(
#                     _('Necessary Requirements To Run This Operation Is '
#                       'Not Satisfied'))
