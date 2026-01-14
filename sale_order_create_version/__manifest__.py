# -*- coding: utf-8 -*-
{
    'name': "Sale Order Create Version Button",
    'summary': """Sale Order Create Version Button""",

    'description': """
        In the Sales Application, In the quotation and sales order form, please add a button called "Create Version", 
        when pressed it should create a new version of the sales order with the same contents and the status 
        for this version "quotation", and the sales order reference should be the old sales order reference with 
        "Rev serial number" for example S0005 REV 1, then if pressed the button again the order reference should be S0005 REV 2 and so on,
    """,


    'author': "IMC",
    'category': 'Sales',
    'version': '17.0',
    # any module necessary for this one to work correctly
    'depends': ['base','sale', 'sale_management','sale_pdf_quote_builder','sale_loyalty'],

    'data': [
        # 'security/ir.model.access.csv',
        'security/security.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
    'task_id': ['3134', '3328', '3329'],

}
