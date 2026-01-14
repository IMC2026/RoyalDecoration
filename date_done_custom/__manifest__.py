{
    'name': "Effictive Date",
    'summary': "Custom Effictive Date In Invontery",
    'description': """Custom Effictive Date In Invontery""",
    'sequence': -33,
    'author': "IMC",
    'website': "www.imc.com",
    'category': 'Inventory',
    'version': '0.1',
    'depends': ['base', 'stock'],

    'data': [
        'security/wizerd.xml',
        'security/ir.model.access.csv',
        'views/wizerd.xml',
        'views/views.xml',

    ],
    'installable': True,
    'application': True,

}
