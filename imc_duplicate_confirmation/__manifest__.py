{
    'name': 'Duplicate Confirmation',
    'version': '17.0.1.0.0',
    'category': 'Base',
    'summary': 'Add confirmation dialog when duplicating records',
    'description': """
        This module adds a confirmation dialog when duplicating any record in the system,
        similar to the delete confirmation behavior.
    """,
    'author': 'IMC Team , Beshoy Wageh',
    'website': 'https://www.imconsult-jo.com',
    'depends': ['web'],
    'data': [],
    'assets': {
        'web.assets_backend': [
            '/imc_duplicate_confirmation/static/src/js/form_controller.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': "OPL-1",
}