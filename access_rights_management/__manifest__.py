# -*- coding: utf-8 -*-
{
    'name': "access_rights_management",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "IMC",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'accounting_pdf_reports', 'om_account_budget', 'om_account_asset', 'om_account_daily_reports'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'data/groups.xml',
        'data/menu_item_update.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

