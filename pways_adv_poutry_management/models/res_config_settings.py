from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    poultry_start_date = fields.Datetime(
        string="Poultry Start Date",
        config_parameter='pways_adv_poutry_management.start_date'
    )
    poultry_end_date = fields.Datetime(
        string="Poultry End Date",
        config_parameter='pways_adv_poutry_management.end_date'
    )
