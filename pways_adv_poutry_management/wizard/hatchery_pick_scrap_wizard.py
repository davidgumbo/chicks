from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class HatcheryPickScrapWizard(models.TransientModel):
    _name = 'hatchery.pick.scrap.wizard'
    _description = 'Hatchery Pick Scrap Wizard'

    hatchery_poultry_id = fields.Many2one('hatchery.poultry', string='Hatchery Poultry')
    hatchery_pick_scrap_line_ids = fields.One2many(
        'hatchery.pick.scrap.wizard.line',
        'hatchery_pick_scrap_wizard_id',
        string='Scrap Lines'
    )

    @api.model
    def default_get(self, fields_list):
        res = super(HatcheryPickScrapWizard, self).default_get(fields_list)
        
        active_id = self.env.context.get('active_id')
        hatchery_poultry_id = self.env['hatchery.poultry'].browse(active_id)

        if hatchery_poultry_id:
            scrap_lines = []
            for selection in hatchery_poultry_id.hatchery_selection_ids:
                scrap_lines.append((0, 0, {
                    'hatchery_selection_id': selection.id,
                    'lot_id': selection.lot_id.id,
                    'size': selection.size,
                    'date': selection.date,
                    'qty': selection.qty,
                    'production_summary_id': selection.production_summary_id.id,
                    # 'yolk': selection.yolk,
                }))
            res['hatchery_pick_scrap_line_ids'] = scrap_lines
            res['hatchery_poultry_id'] = hatchery_poultry_id.id

        return res

    def create_picking_scrap(self):
        # Get the current company and location (update location IDs as needed)
        user_id = self.env.user
        company_id = self.env.company.id
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company_id)], limit=1)         
        int_type_id = warehouse.int_type_id
        
        location_dest_id = warehouse.lot_stock_id.id
        scrap_location_id = self.env['stock.location'].search([('scrap_location', '=', True)], limit=1).id
        scrap_obj = self.env['stock.scrap']

        if any(line.qty <= 0 for line in self.hatchery_pick_scrap_line_ids):
            raise ValidationError(_('Please enter Qty.'))
        if any(line.qty > 0 for line in self.hatchery_pick_scrap_line_ids):
            moves = []
            lines = []
            for line in self.hatchery_pick_scrap_line_ids:
                location_src_id = line.production_summary_id.production_house_id.location_id.id
                if line.qty > 0:
                    lines.append((0, 0 , {
                        'reference': self.hatchery_poultry_id.name,
                        'origin': self.hatchery_poultry_id.name,
                        'product_id': line.lot_id.product_id.id,
                        'quantity': line.qty,
                        'product_uom_id': line.lot_id.product_id.uom_id.id,
                        'lot_id': line.lot_id.id,
                        'location_id': location_src_id,
                        'location_dest_id': location_dest_id,
                        'picking_type_id' : int_type_id.id,
                        # 'picking_type_id' : self.env.ref('stock.picking_type_out').id,
                        }))
                    moves.append((0, 0, {
                        'product_id': line.lot_id.product_id.id,
                        'name': line.lot_id.product_id.name,
                        'product_uom_qty': line.qty,
                        'product_uom': line.lot_id.product_id.uom_id.id,
                        'location_id': location_src_id,
                        'location_dest_id': location_dest_id,
                        'move_line_ids': lines,
                    }))
            picking_vals = {
                'location_id': location_src_id,
                'location_dest_id': location_dest_id,
                'picking_type_id': int_type_id.id,
                # 'picking_type_id': self.env.ref('stock.picking_type_out').id,
                'move_ids_without_package': moves,
                'hatchery_poultry_id': self.hatchery_poultry_id.id,
            }

            picking_id = self.env['stock.picking'].create(picking_vals)
            picking_id.action_confirm()

        if any(line.waste_qty <= 0 for line in self.hatchery_pick_scrap_line_ids):
            raise ValidationError(_('Please enter Waste Qty.'))
        if any(line.waste_qty > 0 for line in self.hatchery_pick_scrap_line_ids):
            scrap_ids = []
            for line in self.hatchery_pick_scrap_line_ids:
                location_src_id = line.production_summary_id.production_house_id.location_id.id
                if line.waste_qty > 0:
                    scrap_vals = {
                            'product_id': line.lot_id.product_id.id,
                            'scrap_qty': line.waste_qty,
                            'location_id': location_src_id,
                            'scrap_location_id': scrap_location_id,
                            'lot_id': line.lot_id.id,
                            'product_uom_category_id' : line.lot_id.product_id.uom_id.category_id.id,
                            'product_uom_id' : line.lot_id.product_id.uom_id.id,
                            'hatchery_poultry_id': self.hatchery_poultry_id.id,
                        }
                    stock_scrap_id = scrap_obj.sudo().create(scrap_vals)
                    stock_scrap_id.do_scrap()
                    stock_scrap_id.action_validate()

class HatcheryPickScrapWizardLine(models.TransientModel):
    _name = 'hatchery.pick.scrap.wizard.line'
    _description = 'Hatchery Pick Scrap Wizard Line'

    hatchery_pick_scrap_wizard_id = fields.Many2one('hatchery.pick.scrap.wizard', string='Scrap Wizard')
    lot_id = fields.Many2one('stock.lot', string='Lot')
    size = fields.Float(string='Size')
    date = fields.Date(string='Date')
    yolk = fields.Float(string='Yolk')
    production_summary_id = fields.Many2one('production.summary', string='Production Summary')
    qty = fields.Float(string='Qty')
    waste_qty = fields.Float(string='Waste Qty')
    hatchery_selection_id = fields.Many2one('hatchery.selection', string='Selection of Eggs')
