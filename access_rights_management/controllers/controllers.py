# -*- coding: utf-8 -*-
# from odoo import http


# class AccessRightsManagement(http.Controller):
#     @http.route('/access_rights_management/access_rights_management', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/access_rights_management/access_rights_management/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('access_rights_management.listing', {
#             'root': '/access_rights_management/access_rights_management',
#             'objects': http.request.env['access_rights_management.access_rights_management'].search([]),
#         })

#     @http.route('/access_rights_management/access_rights_management/objects/<model("access_rights_management.access_rights_management"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('access_rights_management.object', {
#             'object': obj
#         })

