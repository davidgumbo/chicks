# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime, date
from odoo.exceptions import UserError, ValidationError

class FeedTable(models.Model):
    _name = 'feed.table'
    _description = "Feed Table"
    _rec_name = 'name'
    _order = 'id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Name', default=lambda self: _('New'),copy=False)
    feed_table_line_ids = fields.One2many('feed.table.line', 'feed_table_id')
    state = fields.Selection([("draft","Draft"),("confirm","Confirm"),("approve","Approve"),("cancel","Cancelled")],default='draft')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    date_from = fields.Date(string='Starting Date', default=fields.Date.today())
    date_to = fields.Date(string='End Date')
    chicken_farm_id = fields.Many2one('chicken.house', string="Farm House Name")
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('feed.table') or '/'
        return super(FeedTable, self).create(vals)

    def button_draft(self):
        self.state = "draft"

    def button_cancel(self):
        self.state = "cancel"

    def button_confirm(self):
        self.state = "confirm"

    def button_approve(self):
        self.state = "approve"

    def action_feed_table_xls_rprt(self):
        active_id = self._context.get('active_id')
        active_ids = self._context.get('active_ids')
        return {
            'type': 'ir.actions.act_url',
            'url': f'/project/feed_table_xls_report/%s' % (active_id),
            'target': 'new',
        }

class FeedTableLine(models.Model):
    _name = 'feed.table.line'
    _description = "Feed Table Line"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    feed_table_id = fields.Many2one('feed.table')
    feed_table_product_line_ids = fields.One2many('feed.table.product.line', 'feed_table_line_id')
    name = fields.Char()
    dayofweek = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
        ], 'Day of Week', index=True, default=lambda self: str(datetime.today().weekday()))
    hour_from = fields.Float(string='Work from', index=True,
        help="Start and End time of working.\n"
             "A specific value of 24:00 is interpreted as 23:59:59.999999.")
    hour_to = fields.Float(string='Work to')
    shift = fields.Selection([('morning', 'Morning'),('evening', 'Evening'),('night', 'Night'),], default='morning')
    
    date_from = fields.Date(string='Starting Date')
    date_to = fields.Date(string='End Date')
    product_id = fields.Many2one('product.product')
    product_uom_qty = fields.Float(string="Qty", default=1)
    product_uom = fields.Many2one('uom.uom', string="Uom")

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('feed.table.line') or '/'
        return super(FeedTableLine, self).create(vals)

    @api.onchange('product_id')
    def onchange_product(self):
        for rec in self:
            rec.product_uom = rec.product_id.uom_id.id

    def action_view_feed_table_product_line(self):
        self.ensure_one()
        view = self.env.ref('pways_adv_poutry_management.feed_table_line_form_view')

        return {
            'name': _('Detailed Operations'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'feed.table.line',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
            'context': dict(
                self.env.context,
            ),
        }

    
class FeedTableProductLine(models.Model):
    _name = 'feed.table.product.line'
    _description = "Feed Table Product Line"

    feed_table_line_id = fields.Many2one('feed.table.line')
    product_id = fields.Many2one('product.product')
    qty = fields.Float(string="Qty", default=0)
    uom_id = fields.Many2one('uom.uom', string="Uom")
    location_id = fields.Many2one('stock.location')
    location_dest_id = fields.Many2one('stock.location')
    dayofweek = fields.Selection(related='feed_table_line_id.dayofweek', string="Day of Week", store=True)
    hour_from = fields.Float(related='feed_table_line_id.hour_from', string="Work From", store=True)
    hour_to = fields.Float(related='feed_table_line_id.hour_to', string="Work To", store=True)
    shift = fields.Selection(related='feed_table_line_id.shift', string="Shift", store=True)


    @api.onchange('product_id')
    def onchange_product(self):
        for rec in self:
            rec.uom_id = rec.product_id.uom_id
