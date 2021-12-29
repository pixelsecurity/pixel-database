# -*- coding: utf-8 -*-
{
    'name': 'Labor Customization on Products',
    'summary': '''
        Pixel Security sells its products with labor services included which
        needs to be included on sale order line items
    ''',
    'description': '''
        Phase 1
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
        Phase 2:
            1. Whenever the customer creates a Sales Order with a product that includes Labor, 
                that means, that the labor checkbox in the product template is enabled.
                And the specific labor product/ service is created and named.
                The specific labor product should be grouped into a single line of “labor product“
                in the Sales Order Lines and in the Invoice. No matter how many products with its 
                own labor the customer adds to the Sales Order. Each Labor product should be grouped 
                into the same Labor Product (i.e., Labor with Labor, Repairs with Repairs, etc.)
                    a. If the Products do not have labor (checked) the process should be standard as 
                    Odoo operates by default.
            2. The Labor lines of the previous dev spec should be linked to its product,
                this means that whenever the product is removed from the Sales Order the labor 
                line linked to this product should be removed from the Sales Order Line.
            3. When the labor product for Product A has a Labor Rate of $150 and the Labor Hours
                is 1.5 and for Product B has a Labor Rate of $200 and the Labor Hours is 2 , the grouped 
                line should show the Single Labor Line with the Rate of $150+$200 =$350 and the Labor Hours
                of 1.5+2=3 hours. It should sum it. P leasplease refer to the Combine Labor Example document, 
                example2 y 3
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