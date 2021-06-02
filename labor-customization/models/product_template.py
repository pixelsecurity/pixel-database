# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import datetime, timedelta

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    labor_hours = fields.Float(
        name = 'Labor Hours',
        help = 'The number of hours of labor required for this service'
    )

    labor_product = fields.Many2one(
        name = 'Labor Product',
        comodel_name = 'product.template',
        compute = '_compute_labor_product'
    )
    '''
        labor_rate is a stored, computed field
        rather than a related field so that users
        can manually change a labor rate for
        certain products
    '''
    labor_rate = fields.Float(
        name = 'Labor Rate',
        help = 'Rate of labor for this service',
        compute = '_compute_labor_rate',
        store = True,
        readonly = False,
    )
    custom_labor_rate = fields.Boolean(
        name = 'Custom Labor Rate',
        compute = '_compute_custom_labor_rate'
    )

    include_labor = fields.Boolean(
        name = 'Include Labor',
        help = '''If checked, will add the labor cost as a seperate sale order 
               line when this service is added to a sale order'''
    )

    '''
        Search for a product called 'Labor Product'. If it exists,
        save it as a computed field for the record
    '''
    def _compute_labor_product(self):
        labor_product = self.env['product.template'].search([
            ('name', '=', 'Labor')
        ])
        if not labor_product:
            self.labor_product = None;
            print('Unable to find product called labor_product')
        else:
            self.labor_product = labor_product[0].id

    '''
        Whenever labor_product.list_price changes, update it for 
        all other products. If for some reason labor_product does 
        not exist, then set labor_rate to be 0
    '''
    @api.depends('labor_product.list_price')
    def _compute_labor_rate(self):
        for record in self:

            if record.labor_product is None:
                record.labor_rate = 0
            elif record.custom_labor_rate is False:
                record.labor_rate = record.labor_product.list_price
            else:
                record.labor_rate = record.labor_rate

    @api.depends('labor_rate')
    def _compute_custom_labor_rate(self):
        for record in self:
            '''
                If record.labor_product.write_date is False, then that means 
                that the record has not yet been created.
            '''
            if record.labor_product.write_date:
                '''
                    If the time when the labor_product changed its list_price 
                    was less than 3 seconds ago, assume that this api.depends 
                    was triggered because the list_price in labor_product 
                    changed. If it is greater than 3 seconds, assume that the 
                    user manually changed the product's custom_labor_rate, 
                    which would make the custom_labor_rate false
                '''
                if (datetime.now() - record.labor_product.write_date) <= timedelta(seconds = 3):
                    record.custom_labor_rate = False
                else:
                    record.custom_labor_rate = True
            else:
                '''
                If record.labor_product.write_date is False, then the record
                has not yet been created in the database. So then unless 
                labor_rate was changed from the default of 0, 
                TODO: Check if record.labor_rate == 0 or if it already is the previous amount
                '''
                print('In new product')
                print(record.labor_rate)
                if record.labor_rate == 0:

                    record.custom_labor_rate = False
                    record.labor_rate = record.labor_product.list_price
                else:
                    record.custom_labor_rate = False
            
