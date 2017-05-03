# -*- coding: utf-8 -*-
{
    'name': "Project task project ref CogitoWEB",

    'summary': """
        Cost revenue on tasks""",

    'description': """
        Extension to enable Cost revenue on tasks
    """,

    'author': "Cogito",
    'website': "http://www.cogitoweb.it",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.6',

    # any module necessary for this one to work correctly
    'depends': ['base', 'project', 'sale', 'sale_service'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'wizard/translate_tasks.xml',

        'view/project.xml',
        'view/task.xml',
        'view/issue.xml',
        'view/budget_line.xml',
        'view/order.xml',
        'view/account.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
