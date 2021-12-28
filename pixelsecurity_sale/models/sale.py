# -*- coding: utf-8
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    # compute_field = fields.Float("weeee", compute='calculate_all_labor_lines')
    def organize_lines(self):
        sequence = 0
        parent_line_ids = self.order_line.filtered(lambda l: not l.parent_line_id).sorted('sequence')
        child_line_ids = self.order_line - parent_line_ids
        
        for line in parent_line_ids:
            line.sequence = sequence
            sequence += 10
        for line in child_line_ids:
            line.sequence = line.parent_line_id.sequence + 1
    
    def calculate_all_labor_lines(self):
        labor_lines = {}
        for line in self.order_line:
            if not(line.is_labor_line):
                labor_product = line.product_id.product_tmpl_id.labor_product.product_variant_id
                if(labor_product not in labor_lines):
                    labor_lines[labor_product] = line.calculate_labor(line)
                else:
                    labor_lines[labor_product] += line.calculate_labor(line)
        for product in labor_lines:
            labor_line = self.env['sale.order.line'].search([('order_id','=',self.id),('product_id','=',product.id)])
            labor_line.price_unit = labor_lines[product]
        print("we")
        # self.compute_field = 0
                


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    parent_line_id = fields.Many2one(name='Parent Line',comodel_name='sale.order.line',
        ondelete = 'set null')
    is_labor_line = fields.Boolean(string='Is Labor Cost Line', default=False, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        order_lines = None
        new_lines = []
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
        
            labor = self.calculate_labor(line)

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
            new_lines.append(line)
        return new_lines

    def unlink(self):
        if self._check_line_unlink():
            raise UserError(_('You can not remove an order line once the sales order is confirmed.\nYou should rather set the quantity to 0.'))
        for line in self:
            if(line.product_template_id.include_labor):
                labor_product = line.product_template_id.labor_product.product_variant_id
                labor = self.calculate_labor(line)
                labor_line = self.env['sale.order.line'].search([('order_id','=',line.order_id.id),('product_id','=',labor_product.id)])
                if(labor_line):
                    if(labor_line.price_unit - labor > 0):
                        labor_line.price_unit -= labor
                    else:
                        labor_line.unlink()
        return super(SaleOrderLine, self).unlink()

    def calculate_labor(self, line, delta = None):
        res = 0
        if(delta != None):
            res = line.product_template_id.labor_hours * delta * line.product_template_id.labor_rate
        else:
            res = line.product_template_id.labor_hours * line.product_uom_qty * line.product_template_id.labor_rate
        return res

    def write(self, values):
        print(self.product_uom_qty, self, "weeeee", values)
        if('product_uom_qty' in values):
            old_qty = self.product_uom_qty
            if(self.product_id.product_tmpl_id.include_labor):
                labor_product = self.product_id.product_tmpl_id.labor_product.product_variant_id
                labor_line = self.env['sale.order.line'].search([('order_id','=',self.order_id._origin.id),('product_id','=',labor_product.id)])
                delta = values['product_uom_qty'] - self.product_uom_qty
                labor = self.calculate_labor(self, delta)
                labor_line.price_unit += labor
        res = super(SaleOrderLine, self).write(values)
        return res
