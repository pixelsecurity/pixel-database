# -*- coding: utf-8
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    sort_lines_compute = fields.Float("Sort Lines", compute='sort_lines')

    #Sort Order Lines to put labor lines at the end.
    def sort_lines(self):
        lines = []
        biggestN = 0
        #get the labor lines and also get the biggest sequence number on the OLs.
        for line in self.order_line:
            if(line.sequence >= biggestN):
                biggestN = line.sequence
            if(line.is_labor_line):
                lines.append(line)
        biggestN += 1
        #Set the sequence of the labor lines to the biggest sequence # + 1
        for line in lines:
            line.sequence = biggestN
            biggestN += 1
        self.sort_lines_compute = 0


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
            #Set the parent order and sibling order lines.
            if not order_lines:
                if(vals['order_id']):
                    order = self.env['sale.order'].browse(vals['order_id'])
                    order_lines = order.order_line
            #Get the labor line that belongs to the current product on the line
            labor_line = self.env['sale.order.line'].search([('order_id','=',vals['order_id']),('product_id','=',labor_product.id)])
            #Set the hours that will be added or set to the labor line
            labor_hours = line.product_template_id.labor_hours * line.product_uom_qty
            #If the labor line exist, add the hours, else, create the labor line with the hours.
            if(labor_line):
                labor_line.product_uom_qty += labor_hours
            else:
                self.env['sale.order.line'].create({
                        'order_id': line.order_id.id,
                        'product_id': labor_product.id,
                        'name': labor_product.name,
                        'product_uom': labor_product.uom_id.id,
                        'product_template_id': line.product_template_id.labor_product.id,
                        'product_uom_qty': labor_hours,
                        'sequence': line.sequence + 1,
                        'parent_line_id': line.id,
                        'is_labor_line': True,
                    })
            new_lines.append(line)
        #If there is an order, sort the lines.
        if(order != None):
            order.sort_lines()
        return new_lines

    def unlink(self):
        if self._check_line_unlink():
            raise UserError(_('You can not remove an order line once the sales order is confirmed.\nYou should rather set the quantity to 0.'))
        for line in self:
            #If a labor line exists in the product of the line that will be deleted, substract the corresponding hours from the labor line.
            if(line.product_template_id.include_labor):
                labor_product = line.product_template_id.labor_product.product_variant_id
                labor_line = self.env['sale.order.line'].search([('order_id','=',line.order_id.id),('product_id','=',labor_product.id)])
                labor_hours = line.product_id.product_tmpl_id.labor_hours * line.product_uom_qty
                if(labor_line):
                    #If the substraction of the hours is bigger than 0, then substract them, else, remove the labor line.
                    if(labor_line.product_uom_qty - labor_hours >= 0):
                        labor_line.product_uom_qty -= labor_hours
                    else:
                        if(labor_line not in self):
                            labor_line.unlink()
        return super(SaleOrderLine, self).unlink()

    def write(self, values):
        #If there's a change in the quantity of the OL, add/substract hours to the corresponding labor line.
        if('product_uom_qty' in values):
            if(self.product_id.product_tmpl_id.include_labor):
                labor_product = self.product_id.product_tmpl_id.labor_product.product_variant_id
                labor_line = self.env['sale.order.line'].search([('order_id','=',self.order_id._origin.id),('product_id','=',labor_product.id)])
                delta = values['product_uom_qty'] - self.product_uom_qty 
                labor_hours = self.product_id.product_tmpl_id.labor_hours * delta
                labor_line.product_uom_qty += labor_hours
        res = super(SaleOrderLine, self).write(values)
        return res
