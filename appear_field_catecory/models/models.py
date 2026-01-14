from odoo import models, fields
from odoo.exceptions import UserError

from odoo import models, fields, api



class categoryInherit(models.Model):
    _inherit = 'product.category'
    """Class foe adding qr code generation configuration"""




