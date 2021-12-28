# -*- coding: utf-8
from typing import Sequence
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    compute_field = fields.Float("weeee", compute='sort_lines')
    
    def sort_lines(self):
        lines = []
        labor_lines = []
        big = None
        biggestN = 0
        sequence = 0
        for line in self.order_line:
            if(line.sequence >= biggestN):
                biggestN = line.sequence
                big = line
            if(line.is_labor_line):
                labor_lines.append(line)
            else:
                lines.append(line)
        biggestN += 1
        for line in labor_lines:
            line.sequence = biggestN
            lines.append(line)
            biggestN += 1
        for line in lines:
            line.sequence = sequence
            sequence += 1
        self.compute_field = 0

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
        order = None
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

            if not order_lines:
                if(vals['order_id']):
                    order = self.env['sale.order'].browse(vals['order_id'])
                    order_lines = order.order_line
            labor_line = self.env['sale.order.line'].search([('order_id','=',vals['order_id']),('product_id','=',labor_product.id)])
            labor_hours = line.product_template_id.labor_hours * line.product_uom_qty
            print(line.product_template_id.labor_hours, line.product_uom_qty)
            # print(line.product_uom_qty, "www")
        
            labor = self.calculate_labor(line)

            if(labor_line):
                # labor_line.price_unit += labor
                labor_line.product_uom_qty += labor_hours
                # labor_line.sequence = line.sequence + 1
                print(line.sequence, "ssss")
            else:
                self.env['sale.order.line'].create({
                        'order_id': line.order_id.id,
                        'product_id': labor_product.id,
                        'name': labor_product.name,
                        'product_uom': labor_product.uom_id.id,
                        'product_template_id': line.product_template_id.labor_product.id,
                        'product_uom_qty': labor_hours,
                        # 'product_uom_qty': 1,
                        # 'price_unit': labor,
                        'sequence': line.sequence + 1,
                        'parent_line_id': line.id,
                        'is_labor_line': True,
                    })
            new_lines.append(line)
        if(order != None):
            order.sort_lines()
        return new_lines

    def unlink(self):
        if self._check_line_unlink():
            raise UserError(_('You can not remove an order line once the sales order is confirmed.\nYou should rather set the quantity to 0.'))
        for line in self:
            if(line.product_template_id.include_labor):
                labor_product = line.product_template_id.labor_product.product_variant_id
                labor = self.calculate_labor(line)
                labor_line = self.env['sale.order.line'].search([('order_id','=',line.order_id.id),('product_id','=',labor_product.id)])
                labor_hours = line.product_id.product_tmpl_id.labor_hours * line.product_uom_qty
                if(labor_line):
                    if(labor_line.product_uom_qty - labor_hours > 0):
                        labor_line.product_uom_qty -= labor_hours
                    else:
                        print(labor_line in self, "pop")
                        if(labor_line not in self):
                            labor_line.unlink()
                    # if(labor_line.price_unit - labor > 0):
                    #     labor_line.price_unit -= labor
                    # else:
                    #     labor_line.unlink()
        return super(SaleOrderLine, self).unlink()

    def calculate_labor(self, line, delta = None):
        res = 0
        if(delta != None):
            res = line.product_template_id.labor_hours * delta * line.product_template_id.labor_rate
        else:
            res = line.product_template_id.labor_hours * line.product_uom_qty * line.product_template_id.labor_rate
        return res

    def write(self, values):
        if('product_uom_qty' in values):
            if(self.product_id.product_tmpl_id.include_labor):
                labor_product = self.product_id.product_tmpl_id.labor_product.product_variant_id
                labor_line = self.env['sale.order.line'].search([('order_id','=',self.order_id._origin.id),('product_id','=',labor_product.id)])
                delta = values['product_uom_qty'] - self.product_uom_qty 
                labor_hours = self.product_id.product_tmpl_id.labor_hours * delta
                labor_line.product_uom_qty += labor_hours
                # delta = values['product_uom_qty'] - self.product_uom_qty
                # labor = self.calculate_labor(self, delta)
                # labor_line.price_unit += labor
        res = super(SaleOrderLine, self).write(values)
        return res
