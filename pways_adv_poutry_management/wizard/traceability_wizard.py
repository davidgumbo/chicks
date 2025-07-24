from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class TraceabilityWizard(models.TransientModel):
    _name = 'traceability.wizard'
    _description = 'Traceability Wizard'

    traceability_from = fields.Selection([('lot', 'Lot'), ('location', 'Location')])
    lot_id = fields.Many2one('stock.lot')
    farm_house_id = fields.Many2one('chicken.house')


    def action_open_traceability(self):
        if self.traceability_from == 'lot':
            if not self.lot_id:
                raise ValidationError(_('Please select a lot/serial number.'))            
            action = self.env["ir.actions.actions"]._for_xml_id("stock.action_stock_report")
            action['context'] = {
                'active_id': self.lot_id.id,
                'active_model': "stock.lot",
                'url': "/stock/output_format/stock?active_id=%s&active_model=%s" % (self.lot_id.id, "stock.lot"),
            }
            return action
        elif self.traceability_from == 'location':
            if not self.farm_house_id or not self.farm_house_id.location_id:
                raise ValidationError(_('Please select a farm house with a valid location.'))
            return {
                'type': 'ir.actions.act_window',
                'name': _('Traceability Report'),
                'res_model': 'stock.quant',
                'view_mode': 'tree,form',
                'target': 'current',
                'domain': [('location_id', '=', self.farm_house_id.location_id.id)],
            }
        else:
            raise ValidationError(_('Select traceability from.'))
