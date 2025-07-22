# -*- coding: utf-8 -*-
from odoo import api, fields, models


class RequisitionOrder(models.Model):
    _name = 'requisition.order'
    _description = 'Requisition order'

    requisition_product_id = fields.Many2one(
        'inventory.requisition',
        help='Requisition product.')
    state = fields.Selection(string='State',
                           related='requisition_product_id.state')
    product_id = fields.Many2one('product.product', required=True,
                               help='Product')
    description = fields.Text(string="Description", compute='_compute_name',
                            store=True, readonly=False, precompute=True,
                            help='Product description')
    quantity = fields.Integer(string='Quantity', help='Product quantity')
    uom = fields.Char(related='product_id.uom_id.name',
                     string='Unit of Measure', help='Product unit of measure')
    requisition_type= fields.Text(string='Requisition Type')

    @api.depends('product_id')
    def _compute_name(self):
        for option in self:
            if not option.product_id:
                continue
            product_lang = option.product_id.with_context(
                lang=self.requisition_product_id.employee_id.lang)
            option.description = product_lang.get_product_multiline_description_sale()