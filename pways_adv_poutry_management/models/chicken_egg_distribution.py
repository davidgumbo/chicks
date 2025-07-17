from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import date

class ChickenEggDistribution(models.Model):
    _name = 'chicken.egg.distribution' 
    _description = 'Chicken Egg Distribution'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'product_id'
    _order = 'id desc'

    def _get_default_farm(self):
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)], limit=1)
        return warehouse.lot_stock_id.id if warehouse else False

    name = fields.Char(string='Name', default=lambda self: _('New'),copy=False)
    product_id = fields.Many2one('product.product',string='Product',domain=[('last_product', '=', True)], required=True)
    farm_id = fields.Many2one('stock.location',string='Warehouse', required=True,  default=_get_default_farm)
    user_id = fields.Many2one('res.users',string='User',default=lambda self: self.env.user)
    distribution_date = fields.Datetime(string='Distribution Date', default=fields.Datetime.now)
    on_hand_qty = fields.Float(string='Quantity')
    price = fields.Float(string='Price')
    remaining_qty = fields.Float(string='Remaining Qty', compute='_compute_remaining_qty')
    distribution_line_ids = fields.One2many('chicken.egg.distribution.line','distribution_id',string='Distribution Line',)
    sale_order_count = fields.Integer(compute='_compute_sale_order_count')
    company_id = fields.Many2one('res.company',string='Company',default=lambda self: self.env.company,required=True)
    uom_id = fields.Many2one('uom.uom', string='UOM')
    states = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("confirm", "Confirm"),
            ("approve", "Approve"),
            ("sale_order", "Sale Order"),
            ("cancel", "Cancel"),
        ], default="draft", copy=False)


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('chicken.egg.distribution') or 'New'
        records = super(ChickenEggDistribution, self).create(vals_list)
        return records

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.uom_id = self.product_id.uom_id

    def button_draft(self):
        self.states = "draft"

    def button_confirm(self):
        for record in self:
            if not record.distribution_line_ids:
                raise ValidationError("You must add at least one Distribution Line before confirming.")
           
            quants = self.env['stock.quant'].search([
                ('location_id', '=', record.farm_id.id),
                ('product_id', '=', record.product_id.id)
            ])
            total_qty = sum(quants.mapped('quantity'))

            total_done_qty = sum(record.distribution_line_ids.mapped('done_qty'))
            if total_done_qty > total_qty:
                raise ValidationError(
                    f"Total quantity to distribute ({total_done_qty}) exceeds available stock ({total_qty}) "
                    f"in '{record.farm_id.display_name}' for product '{record.product_id.display_name}'."
                )

            record.states = "confirm"

    def button_approve(self):
        self.states = "approve"
    
    def button_sale_order(self):
        SaleOrder = self.env['sale.order']
        SaleOrderLine = self.env['sale.order.line']

        for record in self:
            quants = self.env['stock.quant'].search([
                ('location_id', '=', record.farm_id.id),
                ('product_id', '=', record.product_id.id)
            ])
            total_qty = sum(quants.mapped('quantity'))

            if total_qty <= 0:
                raise ValidationError(f"The selected warehouse '{record.farm_id.display_name}' has zero stock of '{record.product_id.display_name}'.")

            total_done_qty = sum(record.distribution_line_ids.mapped('done_qty'))
            if total_done_qty > total_qty:
                raise ValidationError(f"Total quantity to distribute ({total_done_qty}) exceeds available stock ({total_qty}) in '{record.farm_id.display_name}' for product '{record.product_id.display_name}'.")

            # Group lines by customer
            customer_line_map = {}
            for line in record.distribution_line_ids:
                if not line.customer_id:
                    raise ValidationError("Customer is required for all distribution lines.")
                customer_line_map.setdefault(line.customer_id.id, []).append(line)

            for customer_id, lines in customer_line_map.items():
                sale_order = SaleOrder.create({
                    'partner_id': customer_id,
                    'date_order': fields.Datetime.now(),
                    'user_id': record.user_id.id,
                    'egg_distribution_id': record.id,
                })

                for line in lines:
                    SaleOrderLine.create({
                        'order_id': sale_order.id,
                        'product_id': record.product_id.id,
                        'product_uom_qty': line.done_qty,
                        'price_unit': line.price,
                        'product_uom': line.uom_id.id or record.product_id.uom_id.id,
                        'name': record.product_id.name,
                    })

            record.states = "sale_order"

    def button_cancel(self):
        self.states = "cancel"

    def action_show_available_qty(self):
        """
        This method opens the stock.quant view to show the available quantity of the selected product
        across all warehouses (locations), regardless of the selected farm.
        """
        # Fetch the stock quant records for the selected product, across all locations
        stock_quants = self.env['stock.quant'].search([
            ('product_id', '=', self.product_id.id),
            ('location_id.usage', '=', 'internal'),
        ])
        
        # If no quant records are found, show a message and return
        if not stock_quants:
            raise UserError(_('No stock quantity found for the selected product in any warehouse.'))

        return {
            'type': 'ir.actions.act_window',
            'name': 'Available Stock Quantities',
            'res_model': 'stock.quant',
            'view_mode': 'list',  # Open in tree (list) view
            'view_id': self.env.ref('stock.view_stock_quant_tree').id,  # Reference to stock.quant tree view
            'domain': [('id', 'in', stock_quants.ids)],  # Filter to show all relevant stock.quants
            'target': 'current',  # Opens within the current window
        }

    def unlink(self):
        for record in self:
            if record.states in ('approve', 'sale_order'):
                raise ValidationError(_("You cannot delete a record that is in 'Approve' or 'Sale Order' state."))
        return super(ChickenEggDistribution, self).unlink()
    
    def _compute_sale_order_count(self):
        order = self.env['sale.order']
        for rec in self:
            rec.sale_order_count = order.search_count([('egg_distribution_id', '=', self.id)])

    def action_open_sale_order(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale Order',
            'res_model': 'sale.order',
            'domain': [('egg_distribution_id', '=', self.id)],
            'view_mode': 'list,form',
            'target': 'current',
        }

    @api.onchange('product_id', 'farm_id')
    def _onchange_product_farm(self):
        """ Automatically update `on_hand_qty` and `price` when `product_id` or `farm_id` changes. """
        for record in self:
            if record.product_id and record.farm_id:
                # Search for the stock quant (on-hand qty) based on product_id and farm_id
                quant = self.env['stock.quant'].search([
                    ('product_id', '=', record.product_id.id),
                    ('location_id', '=', record.farm_id.id)
                ], limit=1)
                record.on_hand_qty = quant.quantity if quant else 0.0
                record.price = record.product_id.lst_price  # Get the selling price of the product
            else:
                record.on_hand_qty = 0.0
                record.price = 0.0

    @api.depends('on_hand_qty', 'distribution_line_ids.done_qty')
    def _compute_remaining_qty(self):
        for record in self:
            total_done = sum(record.distribution_line_ids.mapped('done_qty'))
            record.remaining_qty = record.on_hand_qty - total_done


class ChickenEggDistributionLine(models.Model):
    _name = 'chicken.egg.distribution.line' 
    _description = 'Chicken Egg Distribution'

    distribution_id = fields.Many2one('chicken.egg.distribution',string='Distribution',)
    mobile_number = fields.Char(string='Phone Number')
    location_id = fields.Many2one('stock.location',string='Location')
    done_qty = fields.Float(string='Qty',default=1)
    price = fields.Float(string='Price', default=1)
    sub_total = fields.Float(string='Sub Total', compute='_compute_sub_total')
    customer_id = fields.Many2one('res.partner',string='Customer', required=True)
    uom_id = fields.Many2one('uom.uom', string='UOM', related='distribution_id.uom_id',)
    @api.depends('done_qty', 'price')
    def _compute_sub_total(self):
        for line in self:
            line.sub_total = line.done_qty * line.price



class Saleorder(models.Model):
    _inherit = "sale.order"

    egg_distribution_id = fields.Many2one('chicken.egg.distribution' ,string="Poultry")