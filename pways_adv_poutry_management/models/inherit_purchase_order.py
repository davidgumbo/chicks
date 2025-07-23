# -*- coding:utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import date
from odoo import SUPERUSER_ID


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    chicken_farm_id = fields.Many2one('chicken.house', string="Farm House Name")
    is_chicken = fields.Boolean(string='Field Label')
    farm_id = fields.Many2one('incomming.farm.po',string='Inward Lines')


    def _get_location_picking(self, location_id):
        moves = self.picking_ids.mapped('move_line_ids').filtered(lambda x: x.location_id == location_id)
        return moves.mapped('picking_id').filtered(lambda x: x.state not in ('done', 'cancel'))

    def _create_picking(self):
        if not self.is_chicken:
            super(PurchaseOrder,self)._create_picking()
        else:
            StockPicking = self.env['stock.picking']
            for order in self:
                if any([ptype in ['product', 'consu'] for ptype in order.order_line.mapped('product_id.type')]):
                    pickings = order.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
                    location_ids = order.order_line.mapped('line_chicken_house_id.location_id')
                    if location_ids:
                        for location in location_ids:
                            pickings = order._get_location_picking(location)
                            if not pickings:
                                res = order._prepare_picking()
                                res['location_dest_id'] = location.id
                                picking = StockPicking.create(res)
                            else:
                                picking = pickings[0]
                            moves = order.order_line.filtered(lambda x: x.line_chicken_house_id.location_id == location)._create_stock_moves(picking)
                            moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))._action_confirm()
                            seq = 0
                            for move in sorted(moves, key=lambda move: move.date):
                                seq += 5
                                move.sequence = seq
                            moves._action_assign()
                            picking.message_post_with_source('mail.message_origin_link', render_values={'self': picking, 'origin': order}, subtype_xmlid='mail.mt_note',)
                    else:
                        pickings = order.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
                        if not pickings:
                            res = order._prepare_picking()
                            picking = StockPicking.with_user(SUPERUSER_ID).create(res)
                        else:
                            picking = pickings[0]
                        moves = order.order_line._create_stock_moves(picking)
                        moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))._action_confirm()
                        seq = 0
                        for move in sorted(moves, key=lambda move: move.date):
                            seq += 5
                            move.sequence = seq
                        moves._action_assign()
                        picking.message_post_with_source('mail.message_origin_link', render_values={'self': picking, 'origin': order}, subtype_xmlid='mail.mt_note',)
        return True

    @api.onchange('chicken_farm_id','order_line')
    def _onchange_line_chicken(self):
        for rec in self.order_line:
            if self.chicken_farm_id:
                rec.line_chicken_house_id = self.chicken_farm_id.id


    @api.onchange('is_chicken','order_line')
    def _onchange_is_chicken(self):
        for rec in self.order_line:
            if self.is_chicken:
                rec.is_chicken = True
            else:
                rec.is_chicken = False

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    line_chicken_house_id = fields.Many2one('chicken.house' , string="Farm House Name")
    is_chicken = fields.Boolean(string="Chicken")

    def _prepare_stock_move_vals(self, picking, price_unit, product_uom_qty, product_uom):
        self.ensure_one()
        self._check_orderpoint_picking_type()
        product = self.product_id.with_context(lang=self.order_id.dest_address_id.lang or self.env.user.lang)
        date_planned = self.date_planned or self.order_id.date_planned

        if self.line_chicken_house_id:
            location_dest_id = self.line_chicken_house_id.location_id.id 
        else:
            location_dest_id = (self.orderpoint_id and not (self.move_ids | self.move_dest_ids)) and self.orderpoint_id.location_id.id or self.order_id._get_destination_location()

        return {
            'name': (self.product_id.display_name or '')[:2000],
            'product_id': self.product_id.id,
            'date': date_planned,
            'date_deadline': date_planned,
            'location_id': self.order_id.partner_id.property_stock_supplier.id,
            'location_dest_id': location_dest_id,
            'picking_id': picking.id,
            'partner_id': self.order_id.dest_address_id.id,
            'move_dest_ids': [(4, x) for x in self.move_dest_ids.ids],
            'state': 'draft',
            'purchase_line_id': self.id,
            'company_id': self.order_id.company_id.id,
            'price_unit': price_unit,
            'picking_type_id': self.order_id.picking_type_id.id,
            'group_id': self.order_id.group_id.id,
            'origin': self.order_id.name,
            'description_picking': product.description_pickingin or self.name,
            'propagate_cancel': self.propagate_cancel,
            'warehouse_id': self.order_id.picking_type_id.warehouse_id.id,
            'product_uom_qty': product_uom_qty,
            'product_uom': product_uom.id,
            'product_packaging_id': self.product_packaging_id.id,
            'sequence': self.sequence,
        }