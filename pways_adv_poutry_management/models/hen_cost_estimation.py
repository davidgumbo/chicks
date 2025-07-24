# -*- coding: utf-8 -*-
import random
from odoo import api, fields, models, _
from datetime import datetime, date
from odoo.exceptions import UserError, ValidationError

class HenCostEstimation(models.Model):
    _name = 'hen.cost.estimation'
    _description = "Hen Cost Estimation"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'id desc'

    name = fields.Char(string='Name', default=lambda self: _('New'),copy=False)
    chicken_farm_id = fields.Many2one('chicken.house', string="Farm House Name")
    product_id = fields.Many2one('product.product')
    qty = fields.Float(string="Qty", default=1)
    uom_id = fields.Many2one('uom.uom', string="Uom")
    cost_estimation_line_ids = fields.One2many('hen.cost.estimation.line', 'cost_estimation_id')
    grand_total = fields.Float(string="Total", compute="_compute_grand_total")
    estimated_cost = fields.Float(string="Individual Estimated Cost", compute="_compute_grand_total")
    labour_cost_ids = fields.One2many('labour.cost', 'estimation_id')
    overhad_ids = fields.One2many('hen.overhead', 'estimation_cost_id')
    equipment_cost_ids = fields.One2many('equipment.cost', 'hen_cost_estimation_id')
    labour_total = fields.Float(string='Total', compute='_compute_total')
    overhad_total = fields.Float(string='Total', compute='_compute_overhad_total')
    equipment_total = fields.Float(string='Total', compute='_compute_equipment_total')
    cost_total = fields.Float(string='Cost Total', compute='_compute_cost_total')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('hen.cost.estimation') or 'New'
        records = super(HenCostEstimation, self).create(vals_list)
        return records

    @api.depends('cost_estimation_line_ids')
    def _compute_grand_total(self):
        for record in self:
            total = 0
            for line in record.cost_estimation_line_ids:
                total += line.sub_total
            record.grand_total = total
            record.estimated_cost = record.cost_total / record.qty if record.qty else 0

            
    @api.depends('labour_cost_ids')
    def _compute_total(self):
        total = 0
        for rec in self.labour_cost_ids:
            total += rec.sub_total
        self.labour_total = total         

    
    @api.depends('overhad_ids')
    def _compute_overhad_total(self):
        total = 0
        for rec in self.overhad_ids:
            total += rec.sub_total
        self.overhad_total = total  


    @api.depends('equipment_cost_ids')
    def _compute_equipment_total(self):
        total = 0
        for rec in self.equipment_cost_ids:
            total += rec.sub_total
        self.equipment_total = total 


    @api.depends('labour_total', 'overhad_total', 'equipment_total', 'grand_total')
    def _compute_cost_total(self):
        for record in self:
            record.cost_total = record.grand_total + record.labour_total + record.overhad_total + record.equipment_total


class HenCostEstimationLine(models.Model):
    _name = 'hen.cost.estimation.line'
    _description = "Hen Cost Estimation Line"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    cost_estimation_id = fields.Many2one('hen.cost.estimation')
    product_id = fields.Many2one('product.product')
    qty = fields.Float(string="Qty", default=1)
    uom_id = fields.Many2one('uom.uom', string="Uom")
    price = fields.Float(string="Price")
    sub_total = fields.Float(string='Sub total', compute="_compute_sub_total")

    @api.onchange('product_id')
    def price_onchange_product(self):
        for rec in self:
            rec.uom_id = rec.product_id.uom_id
            rec.price = rec.product_id.lst_price

    @api.depends('price', 'qty')
    def _compute_sub_total(self):
        for rec in self:
            rec.sub_total = rec.price * rec.qty



class LabourCost(models.Model):
    _name = 'labour.cost'
    _description = "Labour Cost"


    estimation_id = fields.Many2one('hen.cost.estimation')
    product_id = fields.Many2one('product.product')
    qty = fields.Float(string="Qty", default=1)
    uom_id = fields.Many2one('uom.uom', string="Uom")
    price = fields.Float(string="Price")
    sub_total = fields.Float(string='Sub total', compute='_compute_sub_total')
    

    @api.onchange('product_id')
    def price_onchange_product(self):
        for rec in self:
            rec.uom_id = rec.product_id.uom_id
            rec.price = rec.product_id.lst_price


    @api.depends('price', 'qty')
    def _compute_sub_total(self):
        for rec in self:
            rec.sub_total = rec.price * rec.qty


    # @api.depends('labour_cost_ids')
    # def _compute_total(self):
    #     total = 0
    #     for rec in self.labour_cost_ids:
    #         total += rec.sub_total
    #     self.total = total 


class HenOverhead(models.Model):
    _name = 'hen.overhead'
    _description = "Overhead Cost"


    estimation_cost_id = fields.Many2one('hen.cost.estimation')
    product_id = fields.Many2one('product.product')
    qty = fields.Float(string="Qty", default=1)
    uom_id = fields.Many2one('uom.uom', string="Uom")
    price = fields.Float(string="Price")
    sub_total = fields.Float(string='Sub total', compute='_compute_sub_total')

    @api.onchange('product_id')
    def price_onchange_product(self):
        for rec in self:
            rec.uom_id = rec.product_id.uom_id
            rec.price = rec.product_id.lst_price


    @api.depends('price', 'qty')
    def _compute_sub_total(self):
        for rec in self:
            rec.sub_total = rec.price * rec.qty




class EquipmentCost(models.Model):
    _name = 'equipment.cost'
    _description = "Overhead Cost"


    hen_cost_estimation_id = fields.Many2one('hen.cost.estimation')
    equipment_id = fields.Many2one('maintenance.equipment')
    qty = fields.Float(string="Qty", default=1)
    uom_id = fields.Many2one('uom.uom', string="Uom")
    price = fields.Float(string="Price")
    sub_total = fields.Float(string='Sub total', compute='_compute_sub_total')


    @api.depends('price', 'qty')
    def _compute_sub_total(self):
        for rec in self:
            rec.sub_total = rec.price * rec.qty