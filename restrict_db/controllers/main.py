from odoo import http
from odoo.http import request
from odoo.service import db

import logging

_logger = logging.getLogger(__name__)

class DatabaseManagerController(http.Controller):

    @http.route('/web/database/drop', type='http', auth="none", methods=['POST'], csrf=False)
    def drop(self, master_pwd, name):
        protected_db = 'Royal_Decoration'

        if name == protected_db:
            _logger.exception("Database deletion error.")
            error = "⚠️ Deletion of the PRODUCTION database is blocked by administrator."
            return self._render_template(error=error)


        insecure = odoo.tools.config.verify_admin_password('admin')
        if insecure and master_pwd:
            dispatch_rpc('db', 'change_admin_password', ["admin", master_pwd])
        try:
            dispatch_rpc('db', 'drop', [master_pwd, name])
            if request.session.db == name:
                request.session.logout()
            return request.redirect('/web/database/manager')
        except Exception as e:
            _logger.exception("Database deletion error.")
            error = "Database deletion error: %s" % (str(e) or repr(e))
            return self._render_template(error=error)