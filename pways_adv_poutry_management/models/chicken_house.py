# -*- coding:utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import date


class ChickenHouse(models.Model):
    _name = 'chicken.house'
    _description ="Chicken House" 
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', default=lambda self: _('New'),copy=False)
    house_name = fields.Char(string='Farm House')
    product_id = fields.Many2one("product.product" )
    location_id = fields.Many2one('stock.location', string="Location")
    address = fields.Char(string="Address")
    production_type = fields.Selection([('normal','Normal'),('production','Production')],string='Production Type')
    street = fields.Char(string="street")
    street2 = fields.Char(string="street2")
    city = fields.Char(string="City")
    state_id = fields.Many2one('res.country.state',string="City")
    zip = fields.Char(string="Zip")
    country_id = fields.Many2one('res.country',string="Country")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    latitude = fields.Char(string='latitude')
    longitude = fields.Char(string='longitude') 
    chicken_farm_id = fields.Many2one('chicken.farm',string="Farm Details")
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    states = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("conform", "Conform"),
            ("approve", "Approve"),
            ("cancel", "Cancel"),
        ], default="draft")

    def button_draft(self):
        self.states = "draft"

    def button_conform(self):
        self.states = "conform"

    def button_process(self):
        self.states = "approve"
   
    def button_cancel(self):
        self.states = "cancel"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('chicken.house') or 'New'
        records = super(ChickenHouse, self).create(vals_list)
        return records

# class ChickenBatch(models.Model):
#     _name = 'chicken.batch'
#     _description = 'Batch Management'

#     name = fields.Char(string='Batch Name')
#     house_id = fields.Many2one('chicken.house', string='House')
#     purchase_date = fields.Date(string='Purchase Date')
#     feed_ids = fields.One2many('chicken.feed', 'batch_id', string='Feed Records')
#     cost = fields.Monetary(string='Batch Cost')
#     egg_production = fields.Integer(string='Total Egg Production')
#     death_rate = fields.Float(string='Death Rate (%)')
#     production_days = fields.Integer(string='Production Days')