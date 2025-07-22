from datetime import datetime, timedelta
from odoo import http, fields
from odoo.http import request
from odoo.fields import Datetime as OdooDatetime
from dateutil.relativedelta import relativedelta


class PoultryControllerDashboard(http.Controller):

    @http.route('/dashboard/poultry/count', type='json', auth='user')
    def get_poultry_count(self):
        start_date_str = request.env['ir.config_parameter'].sudo().get_param('pways_adv_poutry_management.start_date')
        end_date_str = request.env['ir.config_parameter'].sudo().get_param('pways_adv_poutry_management.end_date')

        try:
            start_date = OdooDatetime.from_string(start_date_str)
            end_date = OdooDatetime.from_string(end_date_str)
        except Exception:
            end_date = datetime.today()
            start_date = end_date - timedelta(days=30)

        data = {
            'incoming_farm_purchase_count': request.env['incomming.farm.po'].sudo().search_count(
                [('state', '=', 'draft'), ('date', '>=', start_date), ('date', '<=', end_date)]),
            'death_summary_count': request.env['death.summary'].sudo().search_count(
                [('state', '=', 'scrap'), ('date', '>=', start_date), ('date', '<=', end_date)]),
            'feed_table_count': request.env['feed.table'].sudo().search_count(
                [('state', '=', 'approve'), ('date_from', '>=', start_date), ('date_to', '<=', end_date)]),
            'hen_expense_count': request.env['hen.expense'].sudo().search_count(
                [('state', '=', 'done'), ('today_date', '>=', start_date), ('today_date', '<=', end_date)]),
            'inward_transfer_count': request.env['inward.transfer'].sudo().search_count(
                [('state', '=', 'approve'), ('date', '>=', start_date), ('date', '<=', end_date)]),
            'production_summary_count': request.env['production.summary'].sudo().search_count(
                [('state', '=', 'approve'), ('date', '>=', start_date), ('date', '<=', end_date)]),
            'scrap_count': request.env['stock.scrap'].sudo().search_count(
                [('state', '=', 'done'), ('hatchery_poultry_id', '!=', False), ('date_done', '>=', start_date), ('date_done', '<=', end_date)]),
            'cost_estimation_count': request.env['hen.cost.estimation'].sudo().search_count(
                [('start_date', '>=', start_date), ('end_date', '<=', end_date)]),
            'hen_veterinary_count': request.env['hen.veterinary'].sudo().search_count(
                [('state', '=', 'draft'), ('appointment_date', '>=', start_date), ('appointment_date', '<=', end_date)]),
            'hatchery_picking_count': request.env['stock.picking'].sudo().search_count(
                [('state', '=', 'done'), ('hatchery_poultry_id', '!=', False), ('scheduled_date', '>=', start_date), ('scheduled_date', '<=', end_date)]),
            'project_count': request.env['project.project'].sudo().search_count(
                [('poultry', '!=', False), ('date_start', '>=', start_date), ('date', '<=', end_date)]),
            'farm_house_count': request.env['chicken.farm'].sudo().search_count([('states', '=', 'approve')]),
            'inward_farm_house_count': request.env['chicken.house'].sudo().search_count([('production_type', '=', 'normal')]),
            'prodcution_farm_house_count': request.env['chicken.house'].sudo().search_count([('production_type', '=', 'production')]),
            'main_product_count': request.env['product.product'].sudo().search_count([('is_chicken', '=', True)]),
            'final_product_count': request.env['product.product'].sudo().search_count([('last_product', '=', True)]),
            'bill_count': request.env['account.move'].sudo().search_count(
                [('move_type', '=', 'in_invoice'), ('invoice_date', '>=', start_date), ('invoice_date_due', '<=', end_date)]),
            'labour_sheets_count': request.env['account.analytic.line'].sudo().search_count(
                [('date', '>=', start_date), ('date', '<=', end_date)]),
            'hr_employee_count': request.env['hr.employee'].sudo().search_count([]),
            'project_task_count': request.env['project.task'].sudo().search_count(
                [('date_deadline', '>=', start_date), ('date_deadline', '<=', end_date)]),
        }
        return data


class AnimalDashboardController(http.Controller):

    @http.route('/animal/dashboard', type='json', auth='user')
    def _get_animal_dashboard_values(self):
        start_date_str = request.env['ir.config_parameter'].sudo().get_param('pways_adv_poutry_management.start_date')
        end_date_str = request.env['ir.config_parameter'].sudo().get_param('pways_adv_poutry_management.end_date')

        try:
            start_date = OdooDatetime.from_string(start_date_str).date()
            end_date = OdooDatetime.from_string(end_date_str).date()
        except Exception:
            end_date = datetime.today().date()
            start_date = end_date - timedelta(days=30)

        death_monthly_data = [['Month', 'Death']]
        production_monthly_data = [['Month', 'Production']]
        inward_monthly_data = [['Month', 'Production']]
        expenses_monthly_data = [['Month', 'Expenses']]
        final_production_monthly_data = [['Month', 'Final production']]

        death_summary = request.env['death.summary'].search([
            ('date', '>=', start_date),
            ('date', '<=', end_date),
            ('state', '=', 'scrap'),
        ])

        production_data = request.env['production.summary'].search([
            ('date', '>=', start_date),
            ('date', '<=', end_date),
            ('state', '=', 'approve'),
        ])

        inward_data = request.env['incomming.farm.po'].search([
            ('date', '>=', start_date),
            ('date', '<=', end_date),
            ('state', '=', 'done'),
        ])

        expenses_data = request.env['hen.expense'].search([
            ('today_date', '>=', start_date),
            ('today_date', '<=', end_date),
            ('state', '=', 'done'),
        ])

        final_production_data = request.env['stock.picking'].search([
            ('scheduled_date', '>=', start_date),
            ('scheduled_date', '<=', end_date),
            ('picking_type_id.code', '=', 'internal'),
            ('hatchery_poultry_id', '!=', False),
        ])

        current_date = start_date.replace(day=1)

        while current_date <= end_date:
            first_day = current_date
            last_day = (first_day + relativedelta(months=1)) - timedelta(days=1)
            month_name = first_day.strftime('%b %Y')

            death_count = sum(1 for record in death_summary if record.date and first_day <= record.date <= last_day)
            production_count = sum(1 for record in production_data if record.date and first_day <= record.date <= last_day)
            inward_count = sum(1 for record in inward_data if record.date and first_day <= record.date <= last_day)
            expenses_count = sum(1 for record in expenses_data if record.today_date and first_day <= record.today_date <= last_day)
            final_prod_count = sum(1 for record in final_production_data if record.scheduled_date and first_day <= record.scheduled_date.date() <= last_day)

            death_monthly_data.append([month_name, death_count])
            production_monthly_data.append([month_name, production_count])
            inward_monthly_data.append([month_name, inward_count])
            expenses_monthly_data.append([month_name, expenses_count])
            final_production_monthly_data.append([month_name, final_prod_count])

            current_date += relativedelta(months=1)

        return {
            'death_monthly_data': death_monthly_data,
            'production_monthly_data': production_monthly_data,
            'inward_monthly_data': inward_monthly_data,
            'expenses_monthly_data': expenses_monthly_data,
            'final_production_monthly_data': final_production_monthly_data,
        }
