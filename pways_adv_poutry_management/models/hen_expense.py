# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime, date
from odoo.exceptions import UserError, ValidationError

class HenExpense(models.Model):
    _name = 'hen.expense'
    _description = "Hen Expense"
    _rec_name = 'name'
    _order = 'id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def default_get_warehouse(self):
        company = self.env.company
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company.id)], limit=1)
        return warehouse.id if warehouse else False
    
    chicken_farm_id = fields.Many2one('chicken.house', string="Farm House Name")
    production_farm_id = fields.Many2one('chicken.house', string="House Name")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)
    name = fields.Char(string='Name', default=lambda self: _('New'),copy=False)
    partner_id = fields.Many2one("res.partner", string="Customer")
    today_date = fields.Date(default=date.today())
    hen_line_ids = fields.One2many('hen.expense.line', 'argi_expense_id')
    grand_total = fields.Float(string="Total", compute="_compute_grand_total")
    state = fields.Selection([("draft","Draft"),("confirm","Confirm"),("done","Done"),("cancel","Cancelled")],default='draft')
    property_warehouse_id = fields.Many2one('stock.warehouse', string='Default Warehouse', default=default_get_warehouse)
    location_id = fields.Many2one('stock.location', string='Location')
    # location_id = fields.Many2one('stock.location', string='Location')
    location_dest_id = fields.Many2one('stock.location', string='Destination Location', default=lambda self: self.env.ref('stock.stock_location_customers').id,)
    bill_count = fields.Integer(compute="_compute_bill_count")
    picking_count = fields.Integer(compute="_compute_picking_count")
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    production_type = fields.Selection([('normal','Normal'),('production','Production')], string='Production Type')

    # @api.onchange('chicken_farm_id')
    # def _onchange_chicken_location(self):
    #     for rec in self:
    #         if rec.chicken_farm_id:
    #             rec.location_id = rec.chicken_farm_id.location_id.id

    @api.onchange('chicken_farm_id', 'production_farm_id')
    def _onchange_chicken_location(self):
        for rec in self:
            if rec.chicken_farm_id:
                rec.location_id = rec.chicken_farm_id.location_id.id
            elif rec.production_farm_id:
                rec.location_id = rec.production_farm_id.location_id.id
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('argi.expense') or '/'
        return super(HenExpense, self).create(vals)
    
    @api.depends('hen_line_ids')
    def _compute_grand_total(self):
        total = 0
        for rec in self.hen_line_ids:
            total += rec.sub_total
        self.grand_total = total

    def button_draft(self):
        self.state = "draft"

    def button_cancel(self):
        self.state = "cancel"

    def button_done(self):
        self.state = "done"
        move_ids = self.env['stock.move'].search([('hen_expense_id', '=', self.id)])
        move_ids._action_done()

    def button_view_picking(self):
        activities = self.env['stock.picking'].sudo().search([('hen_expense_id', '=', self.id)])
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_all")
        action['domain'] = [('id', 'in', activities.ids)]
        return action

    def button_confirm(self):
        if not self.hen_line_ids:
            raise ValidationError(_('You should have some product lines'))
        self.state = "confirm"
        self. action_create_picking()
        
    def action_create_picking(self):
        lines = []

        if self.property_warehouse_id:
            stock_picking_type =  self.property_warehouse_id
        stock_picking_type =  self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)], limit=1)
        out_type_id = stock_picking_type.out_type_id

        for line in self.hen_line_ids.filtered(lambda x:x.product_id.type in ('product', 'consume')):
            move_id = (0, 0 , {
                    'reference': self.name,
                    'origin': self.name,
                    'product_id': line.product_id.id,
                    'location_id': self.location_id.id,
                    'location_dest_id': self.location_dest_id.id,
                    'quantity': line.qty,
                    'picking_type_id' : out_type_id.id,
                    'product_uom_id': line.product_id.uom_id.id,
                    })
            lines.append(move_id)
        if lines:
            picking_id = self.env['stock.picking'].create({
                        'partner_id': self.company_id.partner_id.id, 
                        'location_id': self.location_id.id,
                        'location_dest_id': self.location_dest_id.id,
                        'picking_type_id': out_type_id.id,
                        'move_line_ids': lines,
                        'hen_expense_id': self.id,
                        'origin': self.name,
                    })
            picking_id.action_confirm()
            return picking_id

    def _compute_bill_count(self):
        for bill in self:
            bill.bill_count = self.env['account.move'].search_count([('hen_expense_id','=', self.id)])
    
    def _compute_picking_count(self):
        for bill in self:
            bill.picking_count = self.env['stock.picking'].search_count([('hen_expense_id','=', self.id)])
    

    def button_create_bill(self):
        invoice_line_list = []
        journal_domain = [('type', '=', 'purchase'), ('company_id', '=', self.env.user.company_id.id),]
        customer_journal_id = self.env['account.journal'].search(journal_domain, limit=1)
        for service in self.hen_line_ids:
            vals = {
                'name': service.product_id.name,
                'product_id': service.product_id.id,
                'price_unit': service.price,
                'quantity': service.qty,
                'product_uom_id': service.uom_id.id,
            }
            invoice_line_list.append((0, 0, vals))
        if invoice_line_list:
            values = {
                'move_type': 'in_invoice',
                'partner_id': self.company_id.partner_id.id,
                'journal_id': customer_journal_id.id,
                'invoice_line_ids': invoice_line_list,
                'invoice_date': date.today(),
                'hen_expense_id': self.id,
            }
            invoice = self.env['account.move'].create(values)

    def action_open_invoice(self):
        invoice_ids = self.env['account.move'].search([('hen_expense_id', '=', self.id)])
        return {
            'name': _('Create Bills'),
            'view_type': 'form',
            'view_mode': 'list,form',
            'view_id': False,
            'res_model': 'account.move',
            'context': "{}",
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', invoice_ids.ids)],
        }
   
class HenExpenseLine(models.Model):
    _name = 'hen.expense.line'
    _description = "Hen Expense Line"

    argi_expense_id = fields.Many2one('hen.expense')
    product_id = fields.Many2one('product.product', required=True)
    qty = fields.Float(string="Qty", default=1)
    uom_id = fields.Many2one('uom.uom', string="Uom")
    price = fields.Float(string="Price")
    sub_total = fields.Float(string='Sub total', compute="_compute_sub_total")
    stock_move_ids = fields.One2many('stock.move', 'hen_expense_line_id', readonly=True)


    @api.onchange('product_id')
    def price_onchange_product(self):
        for rec in self:
            rec.uom_id = rec.product_id.uom_id
            rec.price = rec.product_id.lst_price

    @api.depends('price', 'qty')
    def _compute_sub_total(self):
        for rec in self:
            rec.sub_total = rec.price * rec.qty
