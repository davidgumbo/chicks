# -*- coding: utf-8 -*-
import random
from odoo import api, fields, models, _
from datetime import datetime, date
from odoo.exceptions import UserError, ValidationError

class ProductionSummary(models.Model):
    _name = 'production.summary'
    _description = "Production Summary"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Name', default=lambda self: _('New'),copy=False)
    production_summary_line_ids = fields.One2many('production.summary.line', 'production_summary_id')
    partner_id = fields.Many2one('res.partner')
    date = fields.Date(string='Date', default=fields.Date.today())
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)
    warehouse_id = fields.Many2one('stock.warehouse', domain="[('company_id', '=', company_id)]")
    location_id = fields.Many2one('stock.location')
    picking_count = fields.Integer(compute="_compute_picking_count")
    state = fields.Selection([("draft","Draft"),("confirm","Confirm"),("approve","Approve"),("cancel","Cancelled")],default='draft')
    production_house_id = fields.Many2one('chicken.house')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('production.summary') or '/'
        return super(ProductionSummary, self).create(vals)
       
    def _compute_picking_count(self):
        for picking in self:
            picking.picking_count = self.env['stock.picking'].search_count([('production_summary_id','=', self.id)])
    
    def button_view_picking(self):
        picking_ids = self.env['stock.picking'].search([('production_summary_id', '=', self.id)])
        return {
            'type': 'ir.actions.act_window',
            'name': 'Picking',
            'res_model': 'stock.picking',
            'domain': [('id', 'in', picking_ids.ids)],
            'view_mode': 'list,form',
            'target': 'current',
        }

    def action_create_picking(self):
        moves = []
        lines = []
        in_type_id = self.warehouse_id.in_type_id
        for line in self.production_summary_line_ids:

            move_line_id = (0, 0 , {
                        'reference': self.name,
                        'origin': self.name,
                        'product_id': line.product_id.id,
                        'quantity': line.qty,
                        'product_uom_id': line.product_id.uom_id.id,
                        'chicken_lot_id': line.lot_id.id,
                        # 'lot_name': line.lot_id.name,
                        'location_id': self.partner_id.property_stock_supplier.id,
                        # 'location_dest_id': self.warehouse_id.lot_stock_id.id,
                        'location_dest_id': self.production_house_id.location_id.id,
                        'picking_type_id' : in_type_id.id,
                    })
            lines.append(move_line_id)
            move_id = (0, 0 , {
                        'name': line.product_id.name,
                        'product_id': line.product_id.id,
                        'product_uom_qty': line.qty,
                        'product_uom': line.product_id.uom_id.id,
                        'location_id': self.partner_id.property_stock_supplier.id,
                        # 'location_dest_id': self.warehouse_id.lot_stock_id.id,
                        'location_dest_id': self.production_house_id.location_id.id,
                        'picking_type_id' : in_type_id.id,
                        'move_line_ids': lines,
                    })            
            moves.append(move_id)
        if moves:
            picking_id = self.env['stock.picking'].create({
                    'partner_id': self.partner_id.id, 
                    'location_id': self.partner_id.property_stock_supplier.id,
                    # 'location_dest_id': self.warehouse_id.lot_stock_id.id,
                    'location_dest_id': self.production_house_id.location_id.id,
                    'picking_type_id': in_type_id.id,
                    # 'move_line_ids': lines,
                    'move_ids_without_package': moves,
                    'production_summary_id': self.id,
                    'origin': self.name,
                })
            picking_id.action_confirm()
            return picking_id

    def button_draft(self):
        self.state = "draft"

    def button_cancel(self):
        self.state = "cancel"

    def button_confirm(self):
        self.state = "confirm"

    def button_approve(self):
        self.state = "approve"
        
class ProductionSummaryLine(models.Model):
    _name = 'production.summary.line'
    _description = "Inward Transfer Line"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    production_summary_id = fields.Many2one('production.summary')
    product_id = fields.Many2one('product.product')
    lot_id = fields.Many2one('stock.lot', string='Chicken Lot')
    qty = fields.Float(string="Qty", default=1)
    uom_id = fields.Many2one('uom.uom', string="Uom")

    # @api.onchange('product_id')
    # def onchange_product(self):
    #     for rec in self:
    #         rec.uom_id = rec.product_id.uom_id


    # @api.onchange('lot_id')
    # def onchange_product(self):
    #     for rec in self:
    #         rec.product_id = rec.lot_id.product_id
    #         rec.qty = rec.lot_id.product_qty
    #         rec.uom_id = rec.product_id.uom_id
