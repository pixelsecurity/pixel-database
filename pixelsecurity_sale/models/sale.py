# -*- coding: utf-8
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def write(self, vals):
        ret = super(SaleOrder, self).write(vals)
        orphan_labor_lines = self.mapped('order_line') \
            .filtered(lambda oline: not oline.parent_line_id and oline.is_labor_line)
        orphan_labor_lines.unlink()
        return ret

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    parent_line_id = fields.Many2one(name='Parent Line',comodel_name='sale.order.line',
        ondelete = 'set null')
    is_labor_line = fields.Boolean(string='Is Labor Cost Line', default=False, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        new_lines = super(SaleOrderLine, self).create(vals_list)

        if self.env.context.get('child_product'):
            return new_lines

        for line in new_lines:
            '''
                If a product has a labor product associated with it,
                then add the labor product to the sale order line. 
            '''
            if line.product_template_id.include_labor:
                product = line.product_template_id.labor_product.product_variant_id
                labor_hours = line.product_template_id.labor_hours * line.product_uom_qty
                self.env['sale.order.line'].with_context(child_product=True) \
                    .create({
                        'order_id': line.order_id.id,
                        'product_id': product.id,
                        'name': product.name,
                        'product_uom': product.uom_id.id,
                        'product_template_id': line.product_template_id.labor_product.id,
                        'product_uom_qty': labor_hours,
                        'parent_line_id': line.id,
                        'is_labor_line': True
                    })
        return new_lines

    def write(self, vals):
        result = super(SaleOrderLine, self).write(vals)
        '''
            If recurse_call is None, then this call to
            write was not called by our helper functions
        '''
        if self.env.context.get('recurse_call') is None:
            self._update_sequence()
            self._update_labor_qty()
        return result

    def _update_sequence(self):
        '''
            The sort by write_date orders them such
            that in cases where there are multiple
            orders with the same sequence, the newer
            ones are at the top. This way the newer
            record keeps its sequence, and the older
            records change their sequence
        '''
        parent_line_ids = self.order_id.order_line \
            .filtered(lambda l: not l.parent_line_id) \
            .sorted(lambda l: l.write_date, reverse=True) \
            .sorted(lambda l: l.sequence)

        sequence = 1
        for line in parent_line_ids:
            line.with_context(recurse_call=True).write({
                'sequence': sequence
            })
            if line.product_template_id.include_labor:
                child_line = self.search([
                    ('parent_line_id', '=', line.id)
                ])
                sequence += 1
                child_line.with_context(recurse_call=True).write({
                    'sequence': sequence
                })
            sequence += 1

    def _update_labor_qty(self):
        if self.product_template_id.include_labor:
            labor_hours = self.product_template_id.labor_hours * self.product_uom_qty
            child_line = self.search([
                ('parent_line_id', '=', self.id)
            ])
            child_line.with_context(recurse_call=True).write({
                'product_uom_qty': labor_hours
            })