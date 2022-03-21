# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    labor_hours = fields.Float(string='Labor Hours', default=1,
        help='The number of hours of labor required for this service')
    labor_product = fields.Many2one(string='Labor Product', comodel_name='product.product',
        domain=[('type', '=', 'service')])
    labor_rate = fields.Float(string='Labor Rate', help='Rate of labor for this service',
        related='labor_product.list_price', readonly = True)
    include_labor = fields.Boolean(string='Include Labor', default=False,
        help = 'If checked, will add the a labor cost as a seperate sale order line when this service is added to a sale order')