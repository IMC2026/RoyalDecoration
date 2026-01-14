# -*- coding: utf-8 -*-
{
    'name': 'IMC Duplicate Confirm for Multiple Models',
    'version': '17.0.1.0.0',
    'summary': 'Confirmation popup before duplicating records (Sale, Purchase, Manufacturing, Accounting, Invoices, CRM)',
    'author': 'IMC',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'sale',
        'purchase',
        'mrp',
        'account',
        'crm',
        'stock',
        'product',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/duplicate_confirm_wizard_views.xml',
        'views/sale_order_bindings.xml',
        'views/purchase_order_bindings.xml',
        'views/mrp_production_bindings.xml',
        'views/account_move_bindings.xml',
        # 'views/account_invoice_bindings.xml',
        'views/crm_lead_bindings.xml',
        'views/product_templet.xml'
    ],
    'installable': True,
    'application': False,
}