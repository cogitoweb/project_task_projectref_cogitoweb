# -*- coding: utf-8 -*-
{
    'name': "Project task project ref CogitoWEB",

    'summary': """
        Cost revenue on tasks""",

    'description': """
        Extension to enable Cost revenue on tasks
        
        * Accruals on analaytic lines
        * Budget lines to receipts 
    """,

    'author': "Cogito",
    'website': "http://www.cogitoweb.it",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '2.1',

    # any module necessary for this one to work correctly
    'depends': ['base_cogitoweb', 'account', 'sale_service', 'product', 'hr_contract', 'account_analytic_analysis',
                'analytic_user_function', 'account_analytic_default', 'account_type_cogitoweb',
                'web_tree_many2one_clickable'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizard/translate_tasks.xml',

        'view/task.xml',
        'view/project.xml',
        'view/product_category.xml',
        'view/product_template.xml',
        'view/issue.xml',
        'view/invoice.xml',
        'view/order_line.xml',
        'view/order.xml',
        'view/account.xml',
        'view/account_move.xml',
        'view/account_analytic_line.xml',
        'view/account_analytic_line_accrual.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],

    'application': True,
    'installable': True
}
