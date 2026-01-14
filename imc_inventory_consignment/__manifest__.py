# -*- coding: utf-8 -*-
{
    'name': "IMC Inventory Consignment",

    'summary': """
        IMC Inventory Consignment""",

    'description': """
       IMC Inventory Consignment
    """,

    'author': "IMC",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','stock'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        # 'views/views.xml',
        'views/templates.xml',
    ],

    "post_init_hook": "post_init_hook",
    # only loaded in demonstration mode

}
