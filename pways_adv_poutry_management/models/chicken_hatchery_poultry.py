from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import date

class HatcheryPoultry(models.Model):
    _name = 'hatchery.poultry'
    _description ="Hatchery Poultry"
    _order = 'id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', default=lambda self: _('New'),copy=False)
    date = fields.Date(string='Date', default=date.today())
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    chicken_farm_id = fields.Many2one('chicken.house', string='Farm', required=True)
    destination_id = fields.Many2one('stock.location',string="Destination Location", required=True, default=lambda self: self._default_destination_location())
    
    hatchery_equipment_ids = fields.One2many('hatchery.equipment', 'hatchery_poultry_id', string='Equipments')
    hatchery_equipment_total = fields.Float(string='Total', compute="_compute_grand_total_equipment")
    hatchery_selection_ids = fields.One2many('hatchery.selection', 'hatchery_poultry_id', string='Selection of Eggs')
    hatchery_material_ids = fields.One2many('hatchery.material', 'hatchery_poultry_id', string='Materials')
    hatchery_material_total = fields.Float(string='Total', compute="_compute_grand_total_material")
    hatchery_temperature_ids = fields.One2many('hatchery.temperature', 'hatchery_poultry_id', string='Temperature')
    hatchery_sanitizer_cleaning_ids = fields.One2many('hatchery.sanitizer.cleaning', 'hatchery_poultry_id', string='Sanitizer Cleaning')
    hatchery_fumigation_ids = fields.One2many('hatchery.fumigation', 'hatchery_poultry_id', string='Fumigation')
    hatchery_incubator_ids = fields.One2many('hatchery.incubator', 'hatchery_poultry_id', string='Incubator')
    hatchery_ventilation_ids = fields.One2many('hatchery.ventilation', 'hatchery_poultry_id', string='Ventilation')
    hatchery_turning_ids = fields.One2many('hatchery.turning', 'hatchery_poultry_id', string='Turning')
    hatchery_candings_ids = fields.One2many('hatchery.candings', 'hatchery_poultry_id', string='Candings')

    picking_count = fields.Integer(compute='_compute_picking_count')
    bill_count = fields.Integer(compute='_compute_bill_count')
    scrap_count = fields.Integer(compute='_compute_scrap_count')
    lot_ids = fields.Many2many('stock.lot', string='Lot')
    states = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("confirm", "Confirm"),
            ("process", "Process"),
            ("done", "Done"),
            ("cancel", "Cancel"),
        ], default="draft")

    
    def button_draft(self):
        self.states = "draft"

    def button_conform(self):
        if not self.hatchery_equipment_ids or not self.hatchery_selection_ids or not self.hatchery_material_ids:
            raise ValidationError(_('Please add Some line in Selection of Eggs, Equipments and Materials.'))
        for equipment in self.hatchery_equipment_ids:
            equipment.lot_ids = [(6, 0, self.lot_ids.ids)]
        for material in self.hatchery_material_ids:
            material.lot_ids = [(6, 0, self.lot_ids.ids)]
        self.states = "confirm"

    def button_process(self):
        self.states = "process"

    def button_done(self):
        self.states = "done"
   
    def button_cancel(self):
        self.states = "cancel"


    @api.model
    def _default_destination_location(self):
        company = self.env.company
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company.id)], limit=1)
        return warehouse.lot_stock_id.id if warehouse else False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('hatchery.poultry') or 'New'
        records = super(HatcheryPoultry, self).create(vals_list)
        return records

    ######### compute method ##############
    @api.depends('hatchery_equipment_ids')
    def _compute_grand_total_equipment(self):
        total = 0
        for rec in self.hatchery_equipment_ids:
            total += rec.sub_total
        self.hatchery_equipment_total = total

    @api.depends('hatchery_material_ids')
    def _compute_grand_total_material(self):
        total = 0
        for rec in self.hatchery_material_ids:
            total += rec.sub_total
        self.hatchery_material_total = total

    def _compute_picking_count(self):
        picking = self.env['stock.picking']
        for rec in self:
            rec.picking_count = picking.search_count([('hatchery_poultry_id', '=', self.id)])
        
    def _compute_bill_count(self):
        move = self.env['account.move']
        for rec in self:
            rec.bill_count = move.search_count([('hatchery_poultry_id', '=', self.id)])
        
    def _compute_scrap_count(self):
        move = self.env['stock.scrap']
        for rec in self:
            rec.scrap_count = move.search_count([('hatchery_poultry_id', '=', self.id)])

    ######### State button method ##############

    def action_open_bill(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Bills',
            'res_model': 'account.move',
            'domain': [('hatchery_poultry_id', '=', self.id)],
            'view_mode': 'list,form',
            'target': 'current',
        }

    def action_open_picking(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Pickings',
            'res_model': 'stock.picking',
            'domain': [('hatchery_poultry_id', '=', self.id)],
            'view_mode': 'list,form',
            'target': 'current',
        }

    def action_open_scrap(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Scraps',
            'res_model': 'stock.scrap',
            'domain': [('hatchery_poultry_id', '=', self.id)],
            'view_mode': 'list,form',
            'target': 'current',
        }

    ######### button method ##############
    def action_create_bill(self):
        journal = self.env['account.journal'].sudo().search([('type', '=', 'purchase')], limit=1)
        line_vals = []
        for rec in self:
            if not rec.hatchery_equipment_ids:
                raise ValidationError(_('Add some Product lines.'))
            # analytic_distribution = {str(rec.chicken_farm_id.chicken_farm_id.project_id.analytic_account_id.id): 100}
            for hatchery_equipment_id in rec.hatchery_equipment_ids:
                line_val = {
                    # 'product_id': hatchery_equipment_id.equipment_id.id,
                    'name': hatchery_equipment_id.description,
                    'quantity': hatchery_equipment_id.qty,
                    'product_uom_id': hatchery_equipment_id.uom_id.id,
                    'price_unit': hatchery_equipment_id.unit_price,
                    'lot_ids': hatchery_equipment_id.lot_ids.ids,
                    # 'analytic_distribution': analytic_distribution if analytic_distribution else False,
                }
                line_vals.append((0, 0, line_val))
            vals = {
                'move_type': 'in_invoice',
                'invoice_date': date.today(),
                'journal_id': journal.id,
                'partner_id': rec.user_id.partner_id.id,
                'invoice_line_ids': line_vals,
                'hatchery_poultry_id': self.id,
                'lot_ids': rec.lot_ids.ids,
            }
            self.env['account.move'].sudo().create(vals)

    def action_create_material_bill(self):
        action = self.env["ir.actions.actions"]._for_xml_id("pways_adv_poutry_management.action_hatchery_pick_scrap")
        return action


    def action_create_picking(self):
        company = self.env.company
        default_warehouse = self.env['stock.warehouse'].search([('company_id', '=', company.id)], limit=1)
        # warehouse = self.env['stock.warehouse'].search([('company_id', '=', company.id)], limit=1)
        for rec in self:
            move_lines = []
            for line in rec.hatchery_material_ids:
                move_lines.append((0, 0, {
                    'name': line.product_id.name,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.qty,
                    'product_uom': line.uom_id.id,
                    'location_id': default_warehouse.lot_stock_id.id,
                    'location_dest_id': rec.user_id.partner_id.property_stock_customer.id,
                }))

            # Find the warehouse of destination location
            dest_location = rec.user_id.partner_id.property_stock_customer
            dest_warehouse = self.env['stock.warehouse'].search([
                ('lot_stock_id', 'child_of', dest_location.id),
                ('company_id', '=', company.id)
            ], limit=1)
            picking_vals = {
                'partner_id': rec.user_id.partner_id.id,
                'picking_type_id': dest_warehouse.out_type_id.id if dest_warehouse else default_warehouse.out_type_id.id,
                'location_id': default_warehouse.lot_stock_id.id,
                'move_ids_without_package': move_lines,
                'hatchery_poultry_id': rec.id,
            }
            picking_id = self.env['stock.picking'].create(picking_vals)
            picking_id.action_confirm()

class HatcheryEquipment(models.Model):
    _name = 'hatchery.equipment'
    _description ="Hatchery Equipment"
    _order = 'id desc'

    hatchery_poultry_id = fields.Many2one('hatchery.poultry', string='Hatchery Poultry')
    product_id = fields.Many2one('product.product', string='Product')
    equipment_id = fields.Many2one('maintenance.equipment')
    description = fields.Char(string='Description')
    uom_id = fields.Many2one('uom.uom', string='Uom')
    qty = fields.Float(string='Quantity', default=1)
    unit_price = fields.Float(string='Unit Price')
    sub_total = fields.Float(string='Subtotal', compute="_compute_sub_total")
    lot_ids = fields.Many2many('stock.lot', string='Lot')

    @api.onchange('equipment_id')
    def onchange_product(self):
        for rec in self:
            rec.description = rec.equipment_id.name
            # rec.uom_id = rec.equipment_id.uom_id.id
            # rec.unit_price = rec.equipment_id.lst_price

    @api.depends('unit_price', 'qty')
    def _compute_sub_total(self):
        for rec in self:
            rec.sub_total = rec.unit_price * rec.qty

class HatcherySelection(models.Model):
    _name = 'hatchery.selection'
    _description ="Hatchery Selection of Eggs"
    _order = 'id desc'

    hatchery_poultry_id = fields.Many2one('hatchery.poultry', string='Hatchery Poultry')
    size = fields.Float(string='Size')
    lot_id = fields.Many2one('stock.lot' , string='Lot')
    date = fields.Date(string='Date', default=date.today())
    yolk = fields.Float(string='Yolk')
    qty = fields.Float(string='Qty', compute='_compute_qty', store=True)
    production_summary_id = fields.Many2one('production.summary', string='Production Summary')
    # package_id = fields.Many2one('uom.uom', string='Product')
    # description = fields.Char(string='Description')


    @api.depends('lot_id')
    def _compute_qty(self):
        for record in self:
            record.qty = record.lot_id.product_qty if record.lot_id else 0.0



class HatcheryMaterial(models.Model):
    _name = 'hatchery.material'
    _description ="Hatchery Materials"
    _order = 'id desc'

    hatchery_poultry_id = fields.Many2one('hatchery.poultry', string='Hatchery Poultry')
    product_id = fields.Many2one('product.product', string='Product')
    description = fields.Char(string='Description')
    uom_id = fields.Many2one('uom.uom', string='Uom')
    qty = fields.Float(string='Quantity', default=1)
    unit_price = fields.Float(string='Unit Price')
    sub_total = fields.Float(string='Subtotal', compute="_compute_sub_total")
    lot_ids = fields.Many2many('stock.lot', string='Lot')

    @api.onchange('product_id')
    def onchange_product(self):
        for rec in self:
            rec.description = rec.product_id.name
            rec.uom_id = rec.product_id.uom_id.id
            rec.unit_price = rec.product_id.lst_price

    @api.depends('unit_price', 'qty')
    def _compute_sub_total(self):
        for rec in self:
            rec.sub_total = rec.unit_price * rec.qty

class HatcheryTemperature(models.Model):
    _name = 'hatchery.temperature'
    _description ="Hatchery Temperature"
    _order = 'id desc'

    hatchery_poultry_id = fields.Many2one('hatchery.poultry', string='Hatchery Poultry')
    date = fields.Date(string='Date', default=date.today())
    max_temp = fields.Float(string='Max Temperature')
    min_temp = fields.Float(string='Min Temperature')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    humidity = fields.Float(string='Humidity')
    max_air_rate = fields.Float(string='Maximum Air Rate')
    min_air_rate = fields.Float(string='Minimum Air Rate')


class HatcherySanitizerCleaning(models.Model):
    _name = 'hatchery.sanitizer.cleaning'
    _description ="Hatchery Sanitizer Cleaning"
    _order = 'id desc'

    hatchery_poultry_id = fields.Many2one('hatchery.poultry', string='Hatchery Poultry')
    date = fields.Date(string='Date', default=date.today())
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    sen_in_time = fields.Datetime(string='In Time', default=fields.Datetime.now)
    sen_out_time = fields.Datetime(string='Out Time', default=fields.Datetime.now)


class HatcheryFumigation(models.Model):
    _name = 'hatchery.fumigation'
    _description ="Hatchery Fumigation"
    _order = 'id desc'

    hatchery_poultry_id = fields.Many2one('hatchery.poultry', string='Hatchery Poultry')
    lot_id = fields.Many2one('stock.lot' , string='Lot')
    length = fields.Float(string='Length')
    height = fields.Float(string='Height')
    width = fields.Float(string='Width')
    material = fields.Char(string='Materials')

class HatcheryIncubator(models.Model):
    _name = 'hatchery.incubator'
    _description ="Hatchery Incubator"
    _order = 'id desc'

    hatchery_poultry_id = fields.Many2one('hatchery.poultry', string='Hatchery Poultry')
    incubator_type = fields.Selection([('simple','Simple'),('molt','Molt')],string='Type')
    max_humidity = fields.Float(string='Max Humidity')
    min_humidity = fields.Float(string='Min Humidity')
    max_temp = fields.Float(string='Max Temperature')
    min_temp = fields.Float(string='Min Temperature')
    max_ventilation = fields.Float(string='Max Ventilation')
    min_ventilation = fields.Float(string='Min Ventilation')
    date = fields.Date(string='Date', default=date.today())
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)

class HatcheryVentilation(models.Model):
    _name = 'hatchery.ventilation'
    _description ="Hatchery Ventilation"
    _order = 'id desc'

    hatchery_poultry_id = fields.Many2one('hatchery.poultry', string='Hatchery Poultry')
    name = fields.Char(string='Name')
    max_ventilation = fields.Float(string='Max Ventilation')
    min_ventilation = fields.Float(string='Min Ventilation')
    date = fields.Date(string='Date', default=date.today())
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)

class HatcheryVentilation(models.Model):
    _name = 'hatchery.turning'
    _description ="Hatchery Turning"
    _order = 'id desc'

    hatchery_poultry_id = fields.Many2one('hatchery.poultry', string='Hatchery Poultry')
    turn = fields.Char(string='Turn')
    turn_type = fields.Selection([('hour','Hour'),('day','Day')],string='Type')
    time = fields.Datetime(string='Time', default=fields.Datetime.now)

class HatcheryCandings(models.Model):
    _name = 'hatchery.candings'
    _description ="Hatchery Candings"
    _order = 'id desc'

    hatchery_poultry_id = fields.Many2one('hatchery.poultry', string='Hatchery Poultry')
    equipment_id = fields.Many2one('maintenance.equipment', string='Equipment')
    date = fields.Date(string='Date', default=date.today())
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    name = fields.Char(string='Name')
