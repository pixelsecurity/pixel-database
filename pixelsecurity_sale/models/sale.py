# -*- coding: utf-8
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def organize_lines(self):
        sequence = 0
        parent_line_ids = self.order_line.filtered(lambda l: not l.parent_line_id).sorted('sequence')
        child_line_ids = self.order_line - parent_line_ids
        
        for line in parent_line_ids:
            line.sequence = sequence
            sequence += 10
        for line in child_line_ids:
            line.sequence = line.parent_line_id.sequence + 1




class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    parent_line_id = fields.Many2one(name='Parent Line',comodel_name='sale.order.line',
        ondelete = 'set null')

    is_labor_line = fields.Boolean(string='Is Labor Cost Line', default=False, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        new_lines = []
        for vals in vals_list:
            line = super(SaleOrderLine, self).create(vals)
            '''
            If the line was just created because it is a labor product, can just
            continue.
            '''
            if line.is_labor_line:
                continue
            '''
            If the product doesn't include labor can also just continue 
            '''
            if not line.product_template_id.include_labor:
                continue
            product = line.product_template_id.labor_product.product_variant_id
            labor_hours = line.product_template_id.labor_hours * line.product_uom_qty
            self.env['sale.order.line'].create({
                    'order_id': line.order_id.id,
                    'product_id': product.id,
                    'name': product.name,
                    'product_uom': product.uom_id.id,
                    'product_template_id': line.product_template_id.labor_product.id,
                    'product_uom_qty': labor_hours,
                    'parent_line_id': line.id,
                    'is_labor_line': True,
                    'sequence': line.sequence + 1
                })
            new_lines.append(line)
        return new_lines