# -*- coding:utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import date


class DeathSummary(models.Model):
    _name = 'death.summary'
    _description ="Death Summary"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', default=lambda self: _('New'),copy=False)
    lot_id = fields.Many2one('stock.lot' , string='Batch No:')
    date = fields.Date(string='Date')
    qty = fields.Float()
    summary = fields.Text(string='summary')
    farm_expense_id = fields.Many2one('hen.expense',string='Farm Expense')
    production_type = fields.Selection([('normal','Normal'),('production','Production')],string='Production Type')
    normal_house_id = fields.Many2one('chicken.house')
    production_house_id = fields.Many2one('chicken.house')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    scrap_count = fields.Integer(compute='_compute_scrap_count')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('scrap', 'Scrap'),
        ('cancel', 'Cancel'),
    ], string="Status", default='draft')


    def _compute_scrap_count(self):
        move = self.env['stock.scrap']
        for rec in self:
            rec.scrap_count = move.search_count([('death_summary_id', '=', self.id)])
    
    def button_draft(self):
        self.state = "draft"

    def button_confirm(self):
        self.state = "confirm"

    def button_scrap(self):
        user_id = self.env.user
        
        company_id = self.env.company.id
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company_id)], limit=1)
        
        if not warehouse:
            raise ValidationError(_('No warehouse found for the current company.'))
        
        location_dest_id = warehouse.lot_stock_id.id
        
        scrap_location = self.env['stock.location'].search([('scrap_location', '=', True)], limit=1)
        if not scrap_location:
            raise ValidationError(_('No scrap location defined.'))
        
        scrap_obj = self.env['stock.scrap']
        
        # Validate quantity
        if self.qty <= 0:
            raise ValidationError(_('Please enter a valid quantity.'))
        
        # Determine location source
        location_src_id = None
        if self.normal_house_id:
            location_src_id = self.normal_house_id.location_id.id
        
        if location_src_id:
            picking_vals = {
                'location_id': location_src_id,
                'location_dest_id': location_dest_id,
                'picking_type_id': self.env.ref('stock.picking_type_out').id,
                'move_ids_without_package': [(0, 0, {
                    'product_id': self.lot_id.product_id.id,
                    'name': self.lot_id.product_id.name,
                    'product_uom_qty': self.qty,
                    'product_uom': self.lot_id.product_id.uom_id.id,
                    'location_id': location_src_id,
                    'location_dest_id': location_dest_id,
                })],
            }
            picking_id = self.env['stock.picking'].create(picking_vals)
            picking_id.action_confirm()
            
            scrap_vals = {
                'product_id': self.lot_id.product_id.id,
                'scrap_qty': self.qty,
                'location_id': location_src_id,
                'scrap_location_id': scrap_location.id,
                'lot_id': self.lot_id.id,
                'product_uom_id': self.lot_id.product_id.uom_id.id,
                'death_summary_id': self.id,
            }
            stock_scrap_id = scrap_obj.sudo().create(scrap_vals)
            stock_scrap_id.do_scrap()
            stock_scrap_id.action_validate()
        
        else:
            raise ValidationError(_('Source location is not defined for the normal house.'))

        self.state = 'scrap'
        

    def button_cancel(self):
        self.state = "cancel"

    
    def action_open_scrap(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Scraps',
            'res_model': 'stock.scrap',
            'domain': [('death_summary_id', '=', self.id)],
            'view_mode': 'list,form',
            'target': 'current',
        }


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('death.summary') or 'New'
        records = super(DeathSummary, self).create(vals_list)
        return records
