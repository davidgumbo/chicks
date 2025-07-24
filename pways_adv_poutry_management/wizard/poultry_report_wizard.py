from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class PoultryReportWizard(models.TransientModel):
    _name = 'poultry.report.wizard'
    _description = 'Poultry Report Wizard'


    lot_ids = fields.Many2many('stock.lot', string='Lot')


    def action_generate_report(self):
        tech_ids_str = ','.join(map(str, self.lot_ids.ids))
        url = f'/poultry/poultry_xls_report?lot_ids={tech_ids_str}'
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }