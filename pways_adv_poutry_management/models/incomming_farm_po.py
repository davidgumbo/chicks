# -*- coding:utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import date


class IncommingFarmPO(models.Model):
    _name = 'incomming.farm.po'
    _description ="Incomming Farm PO"
    _order = 'id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', default=lambda self: _('New'),copy=False)
    chicken_farm_id = fields.Many2one('chicken.house', string="Farm House Name")
    location_id = fields.Many2one('stock.location', string="Location")
    date = fields.Date(string="Date", default=fields.Date.context_today)
    incomming_farm_po_line_ids = fields.One2many('incomming.farm.po.lines','incomming_farm_po_id')
    state = fields.Selection([('draft','Draft'),('confirm','Confirm'),('in_order','Purchase'),('done','Done'),('cancel','Cancel')], default='draft', string='State')
    po_count = fields.Integer(compute="_compute_po_count")
    farm_house_id = fields.Many2one('chicken.farm', string='Farm House')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('incomming.farm.po') or 'New'
        records = super(IncommingFarmPO, self).create(vals_list)
        return records

    @api.onchange('chicken_farm_id')
    def _onchange_location(self):
        for rec in self:
            if rec.chicken_farm_id:
                rec.location_id = rec.chicken_farm_id.location_id.id

    def button_draft(self):
        self.state = "draft"

    def button_cancel(self):
        self.state = "cancel"

    def button_confirm(self):
        self.state = "confirm"

    def button_done(self):
        self.state = "done"
        
    def create_farm_purchase_order(self):
        PurchaseOrder = self.env['purchase.order']
        PurchaseOrderLine = self.env['purchase.order.line']
        for rec in self:
            suppliers = {}
            for line in rec.incomming_farm_po_line_ids:
                supplier = line.supplier_id
                if supplier not in suppliers:
                    suppliers[supplier] = []
                suppliers[supplier].append(line)
            for supplier, lines in suppliers.items():
                po_vals = {
                    'partner_id': supplier.id,
                    'date_order': rec.date or fields.Date.today(),
                    # 'chicken_farm_id': rec.chicken_farm_id.id,
                    'is_chicken': True,
                    'farm_id': self.id,
                    'order_line': [],
                }
                for line in lines:
                    po_line_vals = {
                        'product_id': line.product_id.id,
                        'name': line.product_id.display_name,
                        'product_qty': float(line.qty),
                        'product_uom': line.product_id.uom_id.id,
                        'price_unit': line.product_id.standard_price,
                        'date_planned': fields.Date.today(),
                        'line_chicken_house_id': line.normal_house_id.id,
                        'is_chicken': True,
                    }
                    po_vals['order_line'].append((0, 0, po_line_vals))
                PurchaseOrder.create(po_vals)
        self.state = 'in_order'
        return
        
    def _compute_po_count(self):
        for po in self:
            po.po_count = self.env['purchase.order'].search_count([('farm_id','=', self.id)])
    
    def button_view_po(self):
        po_ids = self.env['purchase.order'].search([('farm_id', '=', self.id)])
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Orders',
            'res_model': 'purchase.order',
            'domain': [('id', 'in', po_ids.ids)],
            'view_mode': 'list,form',
            'target': 'current',
        }
    
class IncommingFarmPOLines(models.Model):
    _name = 'incomming.farm.po.lines'
    _description ="Incomming Farm PO Lines"

    incomming_farm_po_id = fields.Many2one('incomming.farm.po',string='Incomming Farm PO')
    product_id = fields.Many2one('product.product')
    supplier_id = fields.Many2one('res.partner')
    qty = fields.Float(string='Quantity') 
    price = fields.Float(string="price")
    sub_total = fields.Float(string="Sub Total" , compute='_sub_total')
    normal_house_id = fields.Many2one('chicken.house', string="Inward Farm House")

    @api.onchange('product_id')
    def _onchange_price(self):
        for rec in self:
            if rec.product_id:
                rec.price = rec.product_id.lst_price

    @api.depends('qty','price')
    def _sub_total(self):
        for rec in self:
            rec.sub_total = rec.qty * rec.price
