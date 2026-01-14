from odoo import models, fields,api

class AddTitleField(models.Model):
    _inherit = 'sale.order'

    title = fields.Char(string="Title")