# -*- coding: utf-8 -*-
import random
from odoo import api, fields, models, _
from datetime import datetime, date
from odoo.exceptions import UserError, ValidationError

class InwardTransfer(models.Model):
    _name = 'inward.transfer'
    _description = "Inward Transfer"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Name', default=lambda self: _('New'),copy=False)
    inward_transfer_line_ids = fields.One2many('inward.transfer.line', 'inward_transfer_id')
    normal_house_id = fields.Many2one('chicken.house')
    production_house_id = fields.Many2one('chicken.house')
    date = fields.Date(string='Date', default=fields.Date.today())
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    picking_count = fields.Integer(compute="_compute_picking_count")
    state = fields.Selection([("draft","Draft"),("confirm","Confirm"),("approve","Approve"),("cancel","Cancelled")],default='draft')
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('inward.transfer') or '/'
        return super(InwardTransfer, self).create(vals)
        
    def _compute_picking_count(self):
        for bill in self:
            bill.picking_count = self.env['stock.picking'].search_count([('inward_transfer_id','=', self.id)])
    
    def button_view_picking(self):
        picking_ids = self.env['stock.picking'].search([('inward_transfer_id', '=', self.id)])
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
        stock_picking_type = self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)], limit=1)
        int_type_id = stock_picking_type.int_type_id

        for line in self.inward_transfer_line_ids:
            move_line_id = (0, 0 , {
                    'reference': self.name,
                    'origin': self.name,
                    'product_id': line.product_id.id,
                    'quantity': line.qty,
                    'product_uom_id': line.product_id.uom_id.id,
                    'lot_id': line.lot_id.id,
                    'location_id': self.normal_house_id.location_id.id,
                    'location_dest_id': self.production_house_id.location_id.id,
                    'picking_type_id' : int_type_id.id,
                    })
            lines.append(move_line_id)
            move_id = (0, 0 , {
                    'name': line.product_id.name,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.qty,
                    'product_uom': line.product_id.uom_id.id,
                    'location_id': self.normal_house_id.location_id.id,
                    'location_dest_id': self.production_house_id.location_id.id,
                    'picking_type_id' : int_type_id.id,
                    'move_line_ids': lines,
                    })            
            moves.append(move_id)
        if moves:
            picking_id = self.env['stock.picking'].create({
                    'partner_id': self.company_id.partner_id.id, 
                    'location_id': self.normal_house_id.location_id.id,
                    'location_dest_id': self.production_house_id.location_id.id,
                    'picking_type_id': int_type_id.id,
                    'move_ids_without_package': moves,
                    'inward_transfer_id': self.id,
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
        
class InwardTransferLine(models.Model):
    _name = 'inward.transfer.line'
    _description = "Inward Transfer Line"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    inward_transfer_id = fields.Many2one('inward.transfer')
    product_id = fields.Many2one('product.product')
    lot_id = fields.Many2one('stock.lot', domain="[('product_id', '=', product_id)]")
    qty = fields.Float(string="Qty", default=1)
    uom_id = fields.Many2one('uom.uom', string="Uom")

    @api.onchange('product_id')
    def price_onchange_product(self):
        for rec in self:
            rec.uom_id = rec.product_id.uom_id
