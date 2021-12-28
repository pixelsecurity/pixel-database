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
    old_qty = fields.Float(string='Old quantity', default=0, store = True)

    @api.model_create_multi
    def create(self, vals_list):
        order_lines = None
        new_lines = []
        labor_lines = {}
        labor_line = None
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
            labor_product = line.product_template_id.labor_product.product_variant_id
            # labor_hours = line.product_template_id.labor_hours * line.product_uom_qty

            if not order_lines:
                if(vals['order_id']):
                    order_lines = self.env['sale.order'].browse(vals['order_id']).order_line
            labor_line = self.env['sale.order.line'].search([('order_id','=',vals['order_id']),('product_id','=',labor_product.id)])
        
            labor = self.calculate_labor(labor_product, line)

            if(labor_line):
                labor_line.price_unit += labor
            else:
                self.env['sale.order.line'].create({
                        'order_id': line.order_id.id,
                        'product_id': labor_product.id,
                        'name': labor_product.name,
                        'product_uom': labor_product.uom_id.id,
                        'product_template_id': line.product_template_id.labor_product.id,
                        # 'product_uom_qty': labor_hours,
                        'product_uom_qty': 1,
                        'price_unit': labor,
                        'parent_line_id': line.id,
                        'is_labor_line': True,
                        'sequence': line.sequence + 1
                    })
                line.old_qty = line.product_uom_qty
            new_lines.append(line)
        return new_lines

    def unlink(self):
        lines_to_unlink = []
        if self._check_line_unlink():
            raise UserError(_('You can not remove an order line once the sales order is confirmed.\nYou should rather set the quantity to 0.'))
        for line in self:
            if(line.product_template_id.include_labor):
                labor_product = line.product_template_id.labor_product.product_variant_id
                labor = self.calculate_labor(labor_product, line)
                labor_line = self.env['sale.order.line'].search([('order_id','=',line.order_id.id),('product_id','=',labor_product.id)])
                if(labor_line):
                    if(labor_line.price_unit - labor > 0):
                        labor_line.price_unit -= labor
                    else:
                        labor_line.unlink()
        return super(SaleOrderLine, self).unlink()

    def calculate_labor(self, labor_product, line, delta = None):
        res = 0
        if(delta):
            res = line.product_template_id.labor_hours * delta * line.product_template_id.labor_rate
        else:
            res = line.product_template_id.labor_hours * line.product_uom_qty * line.product_template_id.labor_rate
        return res

