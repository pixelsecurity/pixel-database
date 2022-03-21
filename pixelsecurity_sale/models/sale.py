# -*- coding: utf-8
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def sort_lines(self):
        if not self._context.get('ignore_sort'):
            for order in self.with_context(ignore_sort=True):
                labor_lines = [line for line in order.order_line if line.is_labor_line]
                biggestN = max(line.sequence for line in order.order_line if not line.is_labor_line)
                for seq, line in enumerate(labor_lines, start=biggestN + 1):
                    line.sequence = seq


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    is_labor_line = fields.Boolean(string='Is Labor Cost Line', default=False, copy=False)
    labor_product_id = fields.Many2one('product.product', string='Labor Product', related='product_id.labor_product')
    include_labor = fields.Boolean(string='Include Labor', related='product_id.include_labor')
    labor_hours = fields.Float(string='Labor Hours', compute='_compute_labor_hours')
    labor_line_id = fields.Many2one(comodel_name='sale.order.line', compute='_compute_labor_hours')

    @api.depends('product_id', 'product_id.labor_product')
    def _compute_labor_hours(self):
        for line in self:
            line.labor_line_id = line.order_id.order_line.filtered(lambda l: l.product_id == line.labor_product_id)
            line.labor_hours = line.product_id.labor_hours * line.product_uom_qty

    @api.model_create_multi
    def create(self, vals_list):
        res = super(SaleOrderLine, self).create(vals_list)
        for line in res:
            if line.is_labor_line or not line.include_labor:
                continue
            if line.labor_line_id:
                line.labor_line_id.product_uom_qty += line.labor_hours
            else:
                line.copy(default={
                    'product_id': line.labor_product_id.id,
                    'name': line.labor_product_id.name,
                    'product_uom': line.labor_product_id.uom_id.id,
                    'product_uom_qty': line.labor_hours,
                    'price_unit': line.labor_product_id.list_price,
                    'is_labor_line': True,
                    'order_id': line.order_id.id
                })
        res.order_id.sort_lines()
        return res

    def unlink(self):
        for line in self:
            if line.include_labor:
                labor_line = line.labor_line_id
                if labor_line and labor_line.product_uom_qty - line.labor_hours > 0:
                    labor_line.product_uom_qty -= line.labor_hours
                else:
                    labor_line.unlink()
        return super(SaleOrderLine, self).unlink()

    def write(self, values):
        if 'product_uom_qty' in values:
            for line in self:
                if line.include_labor:
                    labor_line = line.labor_line_id
                    delta = values['product_uom_qty'] - line.product_uom_qty
                    labor_hours = self.product_id.labor_hours * delta
                    labor_line.product_uom_qty += labor_hours
        res = super(SaleOrderLine, self).write(values)
        self.order_id.sort_lines()
        return res
