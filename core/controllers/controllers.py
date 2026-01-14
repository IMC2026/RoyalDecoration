# -*- coding: utf-8 -*-
# from odoo import http


# class QasiounCore(http.Controller):
#     @http.route('/qasioun_core/qasioun_core', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/qasioun_core/qasioun_core/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('qasioun_core.listing', {
#             'root': '/qasioun_core/qasioun_core',
#             'objects': http.request.env['qasioun_core.qasioun_core'].search([]),
#         })

#     @http.route('/qasioun_core/qasioun_core/objects/<model("qasioun_core.qasioun_core"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('qasioun_core.object', {
#             'object': obj
#         })

