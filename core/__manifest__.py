# -*- coding: utf-8 -*-
{
    'name': "core",

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
    'sequence': -1000,
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'access_rights_management', 'accounting_excel_reports', 'accounting_pdf_reports',
                'hr_employee_transfer', 'hr_employee_updation', 'hr_leave_request_aliasing', 'hr_multi_company',
                'hr_payroll_account_community', 'hr_payroll_community', 'hr_reminder', 'hr_resignation',
                'hr_reward_warning', 'oh_employee_creation_from_user', 'oh_employee_documents_expiry',
                'ohrms_core', 'ohrms_loan', 'ohrms_loan_accounting', 'ohrms_salary_advance', 'om_account_accountant',
                'om_account_asset', 'om_account_budget', 'om_account_daily_reports', 'om_account_followup',
                'om_fiscal_year', 'om_recurring_payments', 'module_auto_update'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/templates.xml',
        'views/views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'application': True,
}
