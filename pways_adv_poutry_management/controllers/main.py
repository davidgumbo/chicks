from datetime import date, datetime, timedelta
from odoo import fields, http
from odoo.http import request
from collections import defaultdict
from dateutil.relativedelta import relativedelta

class PoultryControllerDashboard(http.Controller):

    @http.route('/dashboard/poultry/count', type='json', auth='user')
    def get_poultry_count(self):
        
        current_year = date.today().year
        start_date = date(current_year, 1, 1)
        end_date = date(current_year, 12, 31)

        incoming_farm_purchase_count = request.env['incomming.farm.po'].sudo().search_count(
            [('state', '=', 'draft'),('date', '>=', start_date),('date', '<=', end_date),])
        
        death_summary_count = request.env['death.summary'].sudo().search_count(
            [('state', '=', 'scrap'), ('date', '>=', start_date),('date', '<=', end_date)])
        
        feed_table_count = request.env['feed.table'].sudo().search_count(
            [('state', '=', 'approve'), ('date_from', '>=', start_date),('date_to', '<=', end_date)])
        
        hen_expense_count = request.env['hen.expense'].sudo().search_count(
            [('state', '=', 'done'), ('today_date', '>=', start_date),('today_date', '<=', end_date)])
        
        inward_transfer_count = request.env['inward.transfer'].sudo().search_count(
            [('state', '=', 'approve'), ('date', '>=', start_date), ('date', '<=', end_date)])
        
        production_summary_count = request.env['production.summary'].sudo().search_count(
            [('state', '=', 'approve'), ('date', '>=', start_date),('date', '<=', end_date)])
        
        scrap_count = request.env['stock.scrap'].sudo().search_count(
            [('state', '=', 'done'),('hatchery_poultry_id', '!=', False), ('date_done', '>=', start_date),('date_done', '<=', end_date)])
        
        cost_estimation_count = request.env['hen.cost.estimation'].sudo().search_count([('start_date', '>=', start_date),('end_date', '<=', end_date)])
        
        hen_veterinary_count = request.env['hen.veterinary'].sudo().search_count([('state', '=', 'draft'), ('appointment_date', '>=', start_date),('appointment_date', '<=', end_date)])
        
        hatchery_picking_count = request.env['stock.picking'].sudo().search_count(
            [('state', '=', 'done'),('hatchery_poultry_id', '!=', False), ('scheduled_date', '>=', start_date),
            ('scheduled_date', '<=', end_date)])
        
        project_count = request.env['project.project'].sudo().search_count(
            [('poultry', '!=', False)])

        farm_house_count = request.env['chicken.farm'].sudo().search_count([('states', '=', 'approve')])
        
        inward_farm_house_count = request.env['chicken.house'].sudo().search_count([('production_type', '=', 'normal')])
        
        prodcution_farm_house_count = request.env['chicken.house'].sudo().search_count([('production_type', '=', 'production')])
        
        
        main_product_count = request.env['product.product'].sudo().search_count([('is_chicken', '=', True)])
        
        final_product_count = request.env['product.product'].sudo().search_count([('last_product', '=', True)])
        
        bill_count = request.env['account.move'].sudo().search_count([('move_type', '=', 'in_invoice'), ('invoice_date', '>=', start_date),
            ('invoice_date_due', '<=', end_date)])
        
        labour_sheets_count = request.env['account.analytic.line'].sudo().search_count([('date', '>=', start_date),
            ('date', '<=', end_date)])
        
        hr_employee_count = request.env['hr.employee'].sudo().search_count([])
        
        project_task_count = request.env['project.task'].sudo().search_count([('date_deadline', '>=', start_date),
            ('date_deadline', '<=', end_date)])
          
        
        data = {
            'incoming_farm_purchase_count': incoming_farm_purchase_count,
            'death_summary_count': death_summary_count,
            'feed_table_count': feed_table_count,
            'hen_expense_count': hen_expense_count,
            'inward_transfer_count': inward_transfer_count,
            'production_summary_count': production_summary_count,
            'scrap_count': scrap_count,
            'cost_estimation_count': cost_estimation_count,
            'hen_veterinary_count': hen_veterinary_count,
            'hatchery_picking_count': hatchery_picking_count,
            'project_count': project_count,
            'farm_house_count': farm_house_count,
            'inward_farm_house_count': inward_farm_house_count,
            'prodcution_farm_house_count': prodcution_farm_house_count,
            'main_product_count': main_product_count,
            'final_product_count': final_product_count,
            'bill_count': bill_count,
            'labour_sheets_count': labour_sheets_count,
            'hr_employee_count': hr_employee_count,
            'project_task_count': project_task_count,
            }
        return data



class AnimalDashboardController(http.Controller):

    @http.route('/animal/dashboard', type='json', auth='user')
    def _get_animal_dashboard_values(self):

        current_year = date.today().year
        start_date = date(current_year, 1, 1)
        end_date = date(current_year, 12, 31)

        death_monthly_data = [['Month', 'Death']]
        production_monthly_data = [['Month', 'Production']]
        inward_monthly_data = [['Month', 'Production']]
        expenses_monthly_data = [['Month', 'Expenses']]
        final_production_monthly_data = [['Month', 'Final production']]

        # Fetch records once
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

        # Monthly loop
        current_date = start_date.replace(day=1)

        while current_date <= end_date:
            first_day = current_date
            last_day = (first_day + relativedelta(months=1)) - timedelta(days=1)
            first_day_date = first_day
            last_day_date = last_day
            month_name = first_day.strftime('%b %Y')

            # Death
            monthly_death = sum(
                1 for death in death_summary
                if death.date and first_day_date <= death.date <= last_day_date
            )
            death_monthly_data.append([month_name, monthly_death])

            # Production
            monthly_production = sum(
                1 for production in production_data
                if production.date and first_day_date <= production.date <= last_day_date
            )
            production_monthly_data.append([month_name, monthly_production])

            # Inward
            monthly_inward_data = sum(
                1 for inward in inward_data
                if inward.date and first_day_date <= inward.date <= last_day_date
            )
            inward_monthly_data.append([month_name, monthly_inward_data])

            # Expenses
            monthly_expenses_data = sum(
                1 for expense in expenses_data
                if expense.today_date and first_day_date <= expense.today_date <= last_day_date
            )
            expenses_monthly_data.append([month_name, monthly_expenses_data])

            # Final Production (scheduled_date is datetime)
            monthly_final_production = sum(
                1 for picking in final_production_data
                if picking.scheduled_date and first_day_date <= picking.scheduled_date.date() <= last_day_date
            )
            final_production_monthly_data.append([month_name, monthly_final_production])

            current_date += relativedelta(months=1)

        return {
            'death_monthly_data': death_monthly_data,
            'production_monthly_data': production_monthly_data,
            'inward_monthly_data': inward_monthly_data,
            'expenses_monthly_data': expenses_monthly_data,
            'final_production_monthly_data': final_production_monthly_data,
        }
