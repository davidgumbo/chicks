# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class InventoryRequisition(models.Model):
    _name = 'inventory.requisition'
    _description = 'Inventory Requisition'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Reference No", readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    dept_id = fields.Many2one('hr.department', string='Department',
                             related='employee_id.department_id', store=True)
    user_id = fields.Many2one('res.users', string='Responsible', required=True,
                             domain=lambda self: [('share', '=', False),
                                                  ('id', '!=', self.env.uid)])
    requisition_date = fields.Date(string="Requisition Date",
                                  default=lambda self: fields.Date.today())
    receive_date = fields.Date(string="Received Date", readonly=True)
    requisition_deadline = fields.Date(string="Requisition Deadline")
    company_id = fields.Many2one('res.company', string='Company',
                               default=lambda self: self.env.company)
    requisition_order_ids = fields.One2many('requisition.order',
                                          'requisition_product_id',
                                          required=True)
    confirm_id = fields.Many2one('res.users', string='Confirmed By',
                               default=lambda self: self.env.uid, readonly=True)
    manager_id = fields.Many2one('res.users', string='Department Manager',
                               readonly=True)
    requisition_head_id = fields.Many2one('res.users', string='Approved By',
                                        readonly=True)
    rejected_user_id = fields.Many2one('res.users', string='Rejected By',
                                     readonly=True)
    confirmed_date = fields.Date(string='Confirmed Date', readonly=True)
    department_approval_date = fields.Date(string='Department Approval Date',
                                         readonly=True)
    approval_date = fields.Date(string='Approved Date', readonly=True)
    reject_date = fields.Date(string='Rejection Date', readonly=True)
    source_location_id = fields.Many2one('stock.location',
                                       string='Source Location')
    destination_location_id = fields.Many2one('stock.location',
                                            string="Destination Location")
    internal_picking_id = fields.Many2one('stock.picking.type',
                                         string="Internal Picking")
    requisition_description = fields.Text(string="Reason For Requisition")
    internal_transfer_count = fields.Integer(string='Internal Transfer count',
                                          compute='_compute_internal_transfer_count')
    state = fields.Selection([
        ('new', 'New'),
        ('waiting_department_approval', 'Waiting Department Approval'),
        ('waiting_head_approval', 'Waiting Head Approval'),
        ('approved', 'Approved'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled')], default='new', copy=False, tracking=True)

    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'inventory.requisition') or 'New'
        return super(InventoryRequisition, self).create(vals)

    def action_confirm_requisition(self):
        self.source_location_id = (
            self.employee_id.sudo().department_id.department_location_id.id) if (
            self.employee_id.sudo().department_id.department_location_id) else (
            self.env.ref('stock.stock_location_stock').id)
        self.destination_location_id = (
            self.employee_id.sudo().employee_location_id.id) if (
            self.employee_id.sudo().employee_location_id) else (
            self.env.ref('stock.stock_location_stock').id)
        self.internal_picking_id = (
            self.source_location_id.warehouse_id.int_type_id.id)
        self.write({'state': 'waiting_department_approval'})
        self.confirm_id = self.env.uid
        self.confirmed_date = fields.Date.today()

    def action_department_approval(self):
        self.write({'state': 'waiting_head_approval'})
        self.manager_id = self.env.uid
        self.department_approval_date = fields.Date.today()

    def action_department_cancel(self):
        self.write({'state': 'cancelled'})
        self.rejected_user_id = self.env.uid
        self.reject_date = fields.Date.today()

    def action_head_approval(self):
        self.write({'state': 'approved'})
        self.requisition_head_id = self.env.uid
        self.approval_date = fields.Date.today()

    def action_head_cancel(self):
        self.write({'state': 'cancelled'})
        self.rejected_user_id = self.env.uid
        self.reject_date = fields.Date.today()

    def action_create_internal_transfer(self):
        for rec in self.requisition_order_ids:
            self.env['stock.picking'].create({
                'location_id': self.source_location_id.id,
                'location_dest_id': self.destination_location_id.id,
                'picking_type_id': self.internal_picking_id.id,
                'requisition_order': self.name,
                'move_ids_without_package': [(0, 0, {
                    'name': rec.product_id.name,
                    'product_id': rec.product_id.id,
                    'product_uom': rec.product_id.uom_id.id,
                    'product_uom_qty': rec.quantity,
                    'location_id': self.source_location_id.id,
                    'location_dest_id': self.destination_location_id.id,
                })]
            })
        self.write({'state': 'received'})

    def _compute_internal_transfer_count(self):
        self.internal_transfer_count = self.env['stock.picking'].search_count([
            ('requisition_order', '=', self.name)])

    def get_internal_transfer(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Internal Transfers',
            'view_mode': 'list,form',
            'res_model': 'stock.picking',
            'domain': [('requisition_order', '=', self.name)],
        }

    def action_print_report(self):
        data = {
            'employee': self.employee_id.name,
            'records': self.read(),
            'order_ids': self.requisition_order_ids.read(),
        }
        return self.env.ref(
            'requisition.action_report_inventory_requisition').report_action(
            self, data=data)