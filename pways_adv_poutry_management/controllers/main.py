from datetime import date, datetime, timedelta
from odoo import fields, http
from odoo.http import request
from dateutil.relativedelta import relativedelta
from .date_utils import get_date_range


class PoultryControllerDashboard(http.Controller):

    @http.route('/dashboard/poultry/count', type='json', auth='user')
    def get_poultry_count(self):
        start_date, end_date = get_date_range(request.env)

        counts = {
            'incoming_farm_purchase_count': request.env['incomming.farm.po'].search_count([
                ('state', '=', 'draft'),
                ('date', '>=', start_date),
                ('date', '<=', end_date),
            ]),
            'death_summary_count': request.env['death.summary'].search_count([
                ('state', '=', 'scrap'),
                ('date', '>=', start_date),
                ('date', '<=', end_date),
            ]),
            'feed_table_count': request.env['feed.table'].search_count([
                ('state', '=', 'approve'),
                ('date_from', '>=', start_date),
                ('date_to', '<=', end_date),
            ]),
            'hen_expense_count': request.env['hen.expense'].search_count([
                ('state', '=', 'done'),
                ('today_date', '>=', start_date),
                ('today_date', '<=', end_date),
            ]),
            'inward_transfer_count': request.env['inward.transfer'].search_count([
                ('state', '=', 'approve'),
                ('date', '>=', start_date),
                ('date', '<=', end_date),
            ]),
            'production_summary_count': request.env['production.summary'].search_count([
                ('state', '=', 'approve'),
                ('date', '>=', start_date),
                ('date', '<=', end_date),
            ]),
            'scrap_count': request.env['stock.scrap'].search_count([
                ('state', '=', 'done'),
                ('hatchery_poultry_id', '!=', False),
                ('date_done', '>=', start_date),
                ('date_done', '<=', end_date),
            ]),
            'cost_estimation_count': request.env['hen.cost.estimation'].search_count([
                ('start_date', '>=', start_date),
                ('end_date', '<=', end_date),
            ]),
            'hen_veterinary_count': request.env['hen.veterinary'].search_count([
                ('state', '=', 'draft'),
                ('appointment_date', '>=', start_date),
                ('appointment_date', '<=', end_date),
            ]),
            'hatchery_picking_count': request.env['stock.picking'].search_count([
                ('state', '=', 'done'),
                ('hatchery_poultry_id', '!=', False),
                ('scheduled_date', '>=', start_date),
                ('scheduled_date', '<=', end_date),
            ]),
            'project_count': request.env['project.project'].search_count([
                ('poultry', '!=', False),
                ('date_start', '>=', start_date),
                ('date', '<=', end_date),
            ]),
            'farm_house_count': request.env['chicken.farm'].search_count([
                ('states', '=', 'approve'),
            ]),
            'inward_farm_house_count': request.env['chicken.house'].search_count([
                ('production_type', '=', 'normal'),
            ]),
            'production_farm_house_count': request.env['chicken.house'].search_count([
                ('production_type', '=', 'production'),
            ]),
            'main_product_count': request.env['product.product'].search_count([
                ('is_chicken', '=', True),
            ]),
            'final_product_count': request.env['product.product'].search_count([
                ('last_product', '=', True),
            ]),
            'bill_count': request.env['account.move'].search_count([
                ('move_type', '=', 'in_invoice'),
                ('invoice_date', '>=', start_date),
                ('invoice_date_due', '<=', end_date),
            ]),
            'labour_sheets_count': request.env['account.analytic.line'].search_count([
                ('date', '>=', start_date),
                ('date', '<=', end_date),
            ]),
            'hr_employee_count': request.env['hr.employee'].search_count([]),
            'project_task_count': request.env['project.task'].search_count([
                ('date_deadline', '>=', start_date),
                ('date_deadline', '<=', end_date),
            ]),
        }
        return counts


class AnimalDashboardController(http.Controller):

    @http.route('/animal/dashboard', type='json', auth='user')
    def _get_animal_dashboard_values(self):
        start_date, end_date = get_date_range(request.env)
        start_date = start_date.date()
        end_date = end_date.date()

        # Get base records
        records = {
            'death': request.env['death.summary'].search([
                ('date', '>=', start_date),
                ('date', '<=', end_date),
                ('state', '=', 'scrap'),
            ]),
            'production': request.env['production.summary'].search([
                ('date', '>=', start_date),
                ('date', '<=', end_date),
                ('state', '=', 'approve'),
            ]),
            'inward': request.env['incomming.farm.po'].search([
                ('date', '>=', start_date),
                ('date', '<=', end_date),
                ('state', '=', 'done'),
            ]),
            'expenses': request.env['hen.expense'].search([
                ('today_date', '>=', start_date),
                ('today_date', '<=', end_date),
                ('state', '=', 'done'),
            ]),
            'final_production': request.env['stock.picking'].search([
                ('scheduled_date', '>=', start_date),
                ('scheduled_date', '<=', end_date),
                ('picking_type_id.code', '=', 'internal'),
                ('hatchery_poultry_id', '!=', False),
            ]),
        }

        # Prepare monthly data
        charts = {
            'death': [['Month', 'Death']],
            'production': [['Month', 'Production']],
            'inward': [['Month', 'Inward']],
            'expenses': [['Month', 'Expenses']],
            'final_production': [['Month', 'Final Production']],
        }

        current_date = start_date.replace(day=1)
        while current_date <= end_date:
            month_start = current_date
            month_end = (current_date + relativedelta(months=1)) - timedelta(days=1)
            month_name = current_date.strftime('%b %Y')

            for key in records:
                count = sum(
                    1 for record in records[key]
                    if getattr(record, self._get_date_field(key)) and
                    month_start <= getattr(record, self._get_date_field(key)).date() <= month_end
                )
                charts[key].append([month_name, count])

            current_date += relativedelta(months=1)

        return charts

    def _get_date_field(self, record_type):
        """Helper to get the correct date field for each record type"""
        return {
            'death': 'date',
            'production': 'date',
            'inward': 'date',
            'expenses': 'today_date',
            'final_production': 'scheduled_date',
        }.get(record_type, 'date')
