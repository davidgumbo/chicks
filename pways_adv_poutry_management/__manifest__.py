# -*- coding:utf-8 -*-
{
    'name': 'Advance Poultry Management System',
    'summary': """ Inward chicken purchases,Death summary,Feed schedules,Hatchery,Veterinary,Production,Labour,Costing,Tracebility and following features 
        
        Feed table and schedules
        Farm and Farmhouses Management
        Farm costing, estimation and expenses
        Production summary, veterinary
        Lot and location wise tracebility
        Labour management, 
        Hatchery management
        Eggs distribution with packages
        animal production mangement
        Chicken farm management
        Dashboards Batched wise xls and pdf reports
        Poultry Management System
        
    """,
    'category': 'Industries',
    'author': 'Preciseways Private Limited',
    'version': '17.0',
    'depends': ['base','stock','mrp','sale_management','purchase','product','maintenance','project','hr','hr_timesheet'],
    'data': [
        'security/poultry_groups.xml',
        'security/ir.model.access.csv',
        'data/seq_data.xml',
        'views/assets.xml',
        'wizard/traceability_wizard_view.xml',
        'wizard/hatchery_pick_scrap_wizard_view.xml',
        'wizard/poultry_report_wizard_view.xml',
        'wizard/timesheet_bill_wizard_view.xml',
        'views/dashboard_view.xml',
        'views/chicken_farm_view.xml',
        'views/chicken_house_view.xml',
        'views/incomming_farm_po_view.xml',
        'views/death_summary.xml',
        'views/inherit_purchase_order.xml',
        'views/hen_expense_view.xml',
        'views/stock_view.xml',
        'views/hen_cost_estimation_view.xml',
        'views/feed_table_view.xml',
        'views/inward_transfer_view.xml',
        'views/production_summary_view.xml',
        'views/hen_veterinary_views.xml',
        'views/chicken_hatchery_poultry_view.xml',
        'views/hatchery_view.xml',
        'views/chicken_egg_distribution_view.xml',
        'views/menu.xml',
        ],
 
    'assets': {
       'web.assets_backend': [
            'pways_adv_poutry_management/static/src/css/style.scss',
            'pways_adv_poutry_management/static/src/css/style.css',
            'pways_adv_poutry_management/static/src/js/custom.js',
            'pways_adv_poutry_management/static/src/xml/dashboard.xml',
            "https://www.gstatic.com/charts/loader.js",
            "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/2.9.4/Chart.js",
       ],
    },
 
    "Application": True,
    "installable": True,
    'price': 111.0,
    'currency': 'EUR',
    'images':['static/description/banner.png'],
    'license': 'OPL-1',
}