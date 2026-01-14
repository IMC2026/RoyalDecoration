# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
_logger = logging.getLogger(__name__)
_logger.warning("==== MODULE LOADED ====")


from . import discuss_channel
from . import discuss_channel_member
from . import mail_message
from . import mail_thread
from . import models
from . import res_partner
from . import res_users_settings
from . import whatsapp_account
from . import whatsapp_message
from . import whatsapp_template
from . import whatsapp_template_button
from . import whatsapp_template_variable
