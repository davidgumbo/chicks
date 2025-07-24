# -*- coding:utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import date


class ChickenFarm(models.Model):
    _name = 'chicken.farm' 
    _description = 'Chicken Farm'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', default=lambda self: _('New'),copy=False)
    description = fields.Char(string="Description")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    product_id = fields.Many2one("product.product" ,string="Chicken")
    warehouse_id = fields.Many2one('stock.warehouse',string='Warehouse')
    address = fields.Char(string="Address")
    street = fields.Char(string="street")
    street2 = fields.Char(string="street2")
    city = fields.Char(string="City")
    state_id = fields.Many2one('res.country.state',string="City")
    zip = fields.Char(string="Zip")
    country_id = fields.Many2one('res.country',string="Country")
    house_location_ids = fields.Many2many('chicken.house', string='Locations')
    location_ids = fields.Many2many('stock.location', string='Locations',)
    latitude = fields.Char(string='latitude')
    longitude = fields.Char(string='longitude')
    project_id = fields.Many2one('project.project', string="Project")
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    states = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("confirm", "Confirm"),
            ("approve", "Approve"),
            ("cancel", "Cancel"),
        ], default="draft")


    def button_draft(self):
        self.states = "draft"

    def button_conform(self):
        self.states = "confirm"

    def button_process(self):
        if not self.project_id:
            project_name = f"{self.name} - {self.description}" if self.description else self.name
            project = self.env['project.project'].create({
                'name': project_name,
                'poultry': True,
            })
            self.project_id = project.id
        self.states = "approve"
   
    def button_cancel(self):
        self.states = "cancel"


    @api.onchange('warehouse_id')
    def _onchange_warehouse_id(self):
        if self.warehouse_id:
            # Fetch locations linked to the warehouse
            self.location_ids = self.env['stock.location'].search([
                ('id', 'child_of', self.warehouse_id.lot_stock_id.id)
            ])
        else:
            # Clear the locations if no warehouse is selected
            self.location_ids = False


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('chicken.farm') or 'New'
        records = super(ChickenFarm, self).create(vals_list)
        return records


