# -*- coding: utf-8 -*-
# from odoo import http


# class Mahmoodapproval(http.Controller):
#     @http.route('/make_domin_vendor/make_domin_vendor', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/make_domin_vendor/make_domin_vendor/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('make_domin_vendor.listing', {
#             'root': '/make_domin_vendor/make_domin_vendor',
#             'objects': http.request.env['make_domin_vendor.make_domin_vendor'].search([]),
#         })

#     @http.route('/make_domin_vendor/make_domin_vendor/objects/<model("make_domin_vendor.make_domin_vendor"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('make_domin_vendor.object', {
#             'object': obj
#         })
