from odoo import api, fields, models, _
from datetime import datetime, timedelta

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    hatchery_poultry_id = fields.Many2one('hatchery.poultry', string='Hatchery Poultry')
    hen_expense_id = fields.Many2one('hen.expense')
    inward_transfer_id = fields.Many2one('inward.transfer')
    production_summary_id = fields.Many2one('production.summary')
    production_transfer_id = fields.Many2one('production.transfer')

class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    hatchery_poultry_id = fields.Many2one('hatchery.poultry', string='Hatchery Poultry')
    death_summary_id = fields.Many2one('death.summary', string='Death Summary')


class StockMove(models.Model):
    _inherit = 'stock.move'

    hen_expense_id = fields.Many2one('hen.expense')
    hen_expense_line_id = fields.Many2one('hen.expense.line')

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    chicken_lot_id = fields.Many2one('stock.lot')

class AccountMove(models.Model):
    _inherit = 'account.move'

    hatchery_poultry_id = fields.Many2one('hatchery.poultry', string='Hatchery Poultry')
    hen_expense_id = fields.Many2one('hen.expense')
    argi_expense_line_id = fields.Many2one('hen.expense.line')
    treatment_id = fields.Many2one('hen.treatment')
    vaccination_id = fields.Many2one('hen.vaccination')
    hen_veterinary_id = fields.Many2one('hen.veterinary')
    is_farm_dairy = fields.Boolean(string="Dairy Farm")
    lot_ids = fields.Many2many('stock.lot', string='Lot')
    account_analytic_line_id = fields.Many2one('account.analytic.line')
    project_id = fields.Many2one('project.project', string='Project')
    task_id = fields.Many2one('project.task', string='Project Task')

class ProductProduct(models.Model):
    _inherit = 'product.product'

    is_chicken = fields.Boolean('Main product')
    last_product = fields.Boolean('Final product')



class Project(models.Model):
    _inherit = "project.project"

    poultry = fields.Boolean(string="Poultry")



class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    lot_ids = fields.Many2many('stock.lot', string='Lot')



class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    is_billed = fields.Boolean()




class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
 
    start_date = fields.Datetime(string="Start Date")
    end_date = fields.Datetime(string="End Date")

    @api.model
    def get_values(self):
        res = super().get_values()
        icp = self.env['ir.config_parameter'].sudo()

        start_str = icp.get_param('pways_adv_poutry_management.start_date')
        end_str = icp.get_param('pways_adv_poutry_management.end_date')

        def parse_clean_datetime(dt_str):
            if not dt_str:
                return False
            try:
                return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')

        res.update({
            'start_date': parse_clean_datetime(start_str),
            'end_date': parse_clean_datetime(end_str),
        })
        return res

    def set_values(self):
        super().set_values()
        icp = self.env['ir.config_parameter'].sudo()
        if self.start_date:
            icp.set_param(
                'pways_adv_poutry_management.start_date',
                self.start_date.replace(microsecond=0).strftime('%Y-%m-%d %H:%M:%S')
            )
        if self.end_date:
            icp.set_param(
                'pways_adv_poutry_management.end_date',
                self.end_date.replace(microsecond=0).strftime('%Y-%m-%d %H:%M:%S')
            )



    # start_date = fields.Datetime(config_parameter='pways_adv_poutry_management.start_date', 
    #     string="Start Date",
    #     default=lambda self: datetime.now())
    # end_date = fields.Datetime(config_parameter='pways_adv_poutry_management.end_date', 
    #     string="End Date",
    #     default=lambda self: datetime.now())