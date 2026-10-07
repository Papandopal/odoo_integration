{
    'name': 'Project Integration',
    'version': '1.0.5',
    'summary': 'Import aggregated positions from external API',
    'description': """
        Import aggregated positions from external API
    """,
    'author': 'Evgen',
    'category': 'Tools',
    'depends': ['base', 'web'],
    'data': [
        'data/config_parameters.xml',
        'security/ir.model.access.csv',
        'security/imported_position_rules.xml',
        'views/imported_position_views.xml',
        'views/res_users_views.xml',
        'wizard/import_wizard_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
