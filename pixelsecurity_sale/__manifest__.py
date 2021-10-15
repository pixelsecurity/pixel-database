# -*- coding: utf-8 -*-
{
    'name': 'Labor Customization on Products',
    'summary': '''
        Pixel Security sells its products with labor services included which
        needs to be included on sale order line items
    ''',
    'description': '''
        1. Create 2 new fields on product.template: Labor Hours and Labor Rate
        2. Include a boolean checkbox called 'Include Labor'
        3. Labor Rate field should get its value from a product called Labor,
           however user should be able to override that field on a product by
           product basis. 
        4. When a product that has the boolean 'includes labor' as true, an 
           extra line should be added to the sale order that includes labor,
           and has the labor rate and labor hours from the product. If a
           product has been ordered multiple times, then the labor rate should
           be multiplied accordingly
        5. A new labor SO line should be added for each unique product
    ''',
    'license': 'OPL-1',
    'author': 'Odoo Inc',
    'website': 'https://www.odoo.com',
    'category': 'Development Services/Custom Development',
    'version': '1.0',
    'depends': [
        'sale_management',
        'sale_subscription' # Added because sale_subscription improperly calls
        # create on sale order (without multi) and function needs to be called
        # after this function is
    ],
    'data': [
        'views/product_template_views.xml',
        'views/sale_views.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': False
}