from datetime import date, datetime, timedelta
from odoo import http
from odoo.http import request
from dateutil.relativedelta import relativedelta


# ✅ Flexible date parser to support formats with/without microseconds
def safe_parse_datetime(date_str):
    if not date_str:
        return None
    for fmt in (
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d'
    ):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unrecognized date format: {date_str}")


class PoultryControllerDashboard(http.Controller):

    @http.route('/dashboard/poultry/count', type='json', auth='user')
    def get_poultry_count(self):

        start_date_str = request.env['ir.config_parameter'].sudo().get_param('pways_adv_poutry_management.start_date')
        end_date_str = request.env['ir.config_parameter'].sudo().get_param('pways_adv_poutry_management.end_date')

        try:
            start_date = safe_parse_datetime(start_date_str)
            end_date = safe_parse_datetime(end_date_str)
            if not start_date or not end_date:
                raise ValueError
        except ValueError:
            end_date = datetime.today()
            start_date = end_date - timedelta(days=30)

        env = request.env

        data = {
            'incoming_farm_purchase_count': env['incomming.farm.po'].sudo().search_count(
                [('state', '=', 'draft'), ('date', '>=', start_date), ('date', '<=', end_date)]),
            'death_summary_count': env['death.summary'].sudo().search_count(
                [('state', '=', 'scrap'), ('date', '>=', start_date), ('date', '<=', end_date)]),
            'feed_table_count': env['feed.table'].sudo().search_count(
                [('state', '=', 'approve'), ('date_from', '>=', start_date), ('date_to', '<=', end_date)]),
            'hen_expense_count': env['hen.expense'].sudo().search_count(
                [('state', '=', 'done'), ('today_date', '>=', start_date), ('today_date', '<=', end_date)]),
            'inward_transfer_count': env['inward.transfer'].sudo().search_count(
                [('state', '=', 'approve'), ('date', '>=', start_date), ('date', '<=', end_date)]),
            'production_summary_count': env['production.summary'].sudo().search_count(
                [('state', '=', 'approve'), ('date', '>=', start_date), ('date', '<=', end_date)]),
            'scrap_count': env['stock.scrap'].sudo().search_count(
                [('state', '=', 'done'), ('hatchery_poultry_id', '!=', False), ('date_done', '>=', start_date),
                 ('date_done', '<=', end_date)]),
            'cost_estimation_count': env['hen.cost.estimation'].sudo().search_count(
                [('start_date', '>=', start_date), ('end_date', '<=', end_date)]),
            'hen_veterinary_count': env['hen.veterinary'].sudo().search_count(
                [('state', '=', 'draft'), ('appointment_date', '>=', start_date),
                 ('appointment_date', '<=', end_date)]),
            'hatchery_picking_count': env['stock.picking'].sudo().search_count(
                [('state', '=', 'done'), ('hatchery_poultry_id', '!=', False), ('scheduled_date', '>=', start_date),
                 ('scheduled_date', '<=', end_date)]),
            'project_count': env['project.project'].sudo().search_count(
                [('poultry', '!=', False), ('date_start', '>=', start_date), ('date', '<=', end_date)]),
            'farm_house_count': env['chicken.farm'].sudo().search_count([('states', '=', 'approve')]),
            'inward_farm_house_count': env['chicken.house'].sudo().search_count([('production_type', '=', 'normal')]),
            'prodcution_farm_house_count': env['chicken.house'].sudo().search_count(
                [('production_type', '=', 'production')]),
            'main_product_count': env['product.product'].sudo().search_count([('is_chicken', '=', True)]),
            'final_product_count': env['product.product'].sudo().search_count([('last_product', '=', True)]),
            'bill_count': env['account.move'].sudo().search_count(
                [('move_type', '=', 'in_invoice'), ('invoice_date', '>=', start_date),
                 ('invoice_date_due', '<=', end_date)]),
            'labour_sheets_count': env['account.analytic.line'].sudo().search_count(
                [('date', '>=', start_date), ('date', '<=', end_date)]),
            'hr_employee_count': env['hr.employee'].sudo().search_count([]),
            'project_task_count': env['project.task'].sudo().search_count(
                [('date_deadline', '>=', start_date), ('date_deadline', '<=', end_date)]),
        }

        return data


class AnimalDashboardController(http.Controller):

    @http.route('/animal/dashboard', type='json', auth='user')
    def _get_animal_dashboard_values(self):

        start_date_str = request.env['ir.config_parameter'].sudo().get_param('pways_adv_poutry_management.start_date')
        end_date_str = request.env['ir.config_parameter'].sudo().get_param('pways_adv_poutry_management.end_date')

        try:
            start_date = safe_parse_datetime(start_date_str)
            end_date = safe_parse_datetime(end_date_str)
            if not start_date or not end_date:
                raise ValueError
            start_date = start_date.date()
            end_date = end_date.date()
        except ValueError:
            end_date = datetime.today().date()
            start_date = end_date - timedelta(days=30)

        death_monthly_data = [['Month', 'Death']]
        production_monthly_data = [['Month', 'Production']]
        inward_monthly_data = [['Month', 'Inward']]
        expenses_monthly_data = [['Month', 'Expenses']]
        final_production_monthly_data = [['Month', 'Final production']]

        env = request.env

        death_summary = env['death.summary'].sudo().search(
            [('date', '>=', start_date), ('date', '<=', end_date), ('state', '=', 'scrap')])
        production_data = env['production.summary'].sudo().search(
            [('date', '>=', start_date), ('date', '<=', end_date), ('state', '=', 'approve')])
        inward_data = env['incomming.farm.po'].sudo().search(
            [('date', '>=', start_date), ('date', '<=', end_date), ('state', '=', 'done')])
        expenses_data = env['hen.expense'].sudo().search(
            [('today_date', '>=', start_date), ('today_date', '<=', end_date), ('state', '=', 'done')])
        final_production_data = env['stock.picking'].sudo().search(
            [('scheduled_date', '>=', start_date), ('scheduled_date', '<=', end_date),
             ('picking_type_id.code', '=', 'internal'), ('hatchery_poultry_id', '!=', False)])

        current_date = start_date.replace(day=1)

        while current_date <= end_date:
            first_day = current_date
            last_day = (first_day + relativedelta(months=1)) - timedelta(days=1)
            month_name = first_day.strftime('%b %Y')

            death_monthly_data.append(
                [month_name, sum(1 for d in death_summary if d.date and first_day <= d.date <= last_day)])
            production_monthly_data.append(
                [month_name, sum(1 for p in production_data if p.date and first_day <= p.date <= last_day)])
            inward_monthly_data.append(
                [month_name, sum(1 for i in inward_data if i.date and first_day <= i.date <= last_day)])
            expenses_monthly_data.append(
                [month_name, sum(1 for e in expenses_data if e.today_date and first_day <= e.today_date <= last_day)])
            final_production_monthly_data.append([month_name, sum(1 for f in final_production_data if
                                                                  f.scheduled_date and first_day <= f.scheduled_date.date() <= last_day)])

            current_date += relativedelta(months=1)

        return {
            'death_monthly_data': death_monthly_data,
            'production_monthly_data': production_monthly_data,
            'inward_monthly_data': inward_monthly_data,
            'expenses_monthly_data': expenses_monthly_data,
            'final_production_monthly_data': final_production_monthly_data,
        }
