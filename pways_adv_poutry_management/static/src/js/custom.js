/* @odoo-module */
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useEffect, useRef } from "@odoo/owl";
// import { jsonrpc } from "@web/core/network/rpc_service";
import { rpc } from "@web/core/network/rpc";
class PoultryDashboard extends Component {
    setup() {
        super.setup();
        this.orm = useService('orm');
        // this.rpc = useService("rpc");
        this.actionService = useService("action");
        // this._fetchData();
        // this.fetch():
        this.canvasRef = useRef("canvas");
        this.try();
        this.renderElement();
    }

        // $.when(this._super())
        //     .then(function (ev) {
    // renderElement() {
    //     const self = this;
    //     rpc('/dashboard/poultry/count', {}).then(function (result) {
            // $('#incoming_farm_purchase_count').empty().append(result['incoming_farm_purchase_count']);
            // $('#death_summary_count').empty().append(result['death_summary_count']);
            // $('#feed_table_count').empty().append(result['feed_table_count']);
            // $('#hen_expense_count').empty().append(result['hen_expense_count']);
            // $('#inward_transfer_count').empty().append(result['inward_transfer_count']);
            // $('#production_summary_count').empty().append(result['production_summary_count']);
            // $('#scrap_count').empty().append(result['scrap_count']);
            // $('#cost_estimation_count').empty().append(result['cost_estimation_count']);
            // $('#hen_veterinary_count').empty().append(result['hen_veterinary_count']);
            // $('#hatchery_picking_count').empty().append(result['hatchery_picking_count']);
            // $('#project_count').empty().append(result['project_count']);
            // $('#farm_house_count').empty().append(result['farm_house_count']);
            // $('#inward_farm_house_count').empty().append(result['inward_farm_house_count']);
            // $('#prodcution_farm_house_count').empty().append(result['prodcution_farm_house_count']);
            // $('#main_product_count').empty().append(result['main_product_count']);
            // $('#final_product_count').empty().append(result['final_product_count']);
            // $('#bill_count').empty().append(result['bill_count']);
            // $('#labour_sheets_count').empty().append(result['labour_sheets_count']);
            // $('#hr_employee_count').empty().append(result['hr_employee_count']);
            // $('#project_task_count').empty().append(result['project_task_count']);
    //     });
    // }

    renderElement() {
        const self = this;
        // rpc('/animal/data', {}).then(function (result) {
        rpc('/dashboard/poultry/count', {}).then(function (result) {
            const elementsToUpdate = {
                '#incoming_farm_purchase_count': result['incoming_farm_purchase_count'],
                '#death_summary_count': result['death_summary_count'],
                '#feed_table_count': result['feed_table_count'],
                '#hen_expense_count': result['hen_expense_count'],
                '#inward_transfer_count': result['inward_transfer_count'],
                '#production_summary_count': result['production_summary_count'],
                '#scrap_count': result['scrap_count'],
                '#cost_estimation_count': result['cost_estimation_count'],
                '#hen_veterinary_count': result['hen_veterinary_count'],
                '#hatchery_picking_count': result['hatchery_picking_count'],
                '#project_count': result['project_count'],
                '#farm_house_count': result['farm_house_count'],
                '#inward_farm_house_count': result['inward_farm_house_count'],
                '#prodcution_farm_house_count': result['prodcution_farm_house_count'],
                '#main_product_count': result['main_product_count'],
                '#final_product_count': result['final_product_count'],
                '#bill_count': result['bill_count'],
                '#labour_sheets_count': result['labour_sheets_count'],
                '#hr_employee_count': result['hr_employee_count'],
                '#project_task_count': result['project_task_count'],
               };
            console.log('calllllllllllllllllllllllll.....................',incoming_farm_purchase_count)
            Object.keys(elementsToUpdate).forEach(selector => {
                const element = document.querySelector(selector);
                if (element) {
                    element.textContent = elementsToUpdate[selector];
                } else {
                    console.error(`Element with selector ${selector} not found`);
                }
            });
        });
    }

    view_incoming_farm_purchase(ev) {
        return this.actionService.doAction({
            name:'Incoming Farm Purchase',
            type: 'ir.actions.act_window',
            res_model: 'incomming.farm.po',
            domain: [['state', '=', 'draft']],
            views: [[false, 'list'], [false, 'form']],
            target: 'current'
        });
    }


    view_death_summary(ev) {
        return this.actionService.doAction({
            name:'Death Summary',
            type: 'ir.actions.act_window',
            res_model: 'death.summary',
            domain: [['state', '=', 'scrap']],
            views: [[false, 'list'], [false, 'form']],
            target: 'current'
        });
    }

    view_feed_table(ev) {
        return this.actionService.doAction({
            name:'Inward Feed Table',
            type: 'ir.actions.act_window',
            res_model: 'feed.table',
            domain: [['state', '=', 'approve']],
            views: [[false, 'list'], [false, 'form']],
            target: 'current'
        });
    }

    view_hen_expense(ev) {
        return this.actionService.doAction({
            name:'Expenses',
            type: 'ir.actions.act_window',
            res_model: 'hen.expense',
            domain: [['state', '=', 'done']],
            views: [[false, 'list'], [false, 'form']],
            target: 'current'
        });
    }


    view_inward_transfer(ev) {
        return this.actionService.doAction({
            name:'Production Transfer',
            type: 'ir.actions.act_window',
            res_model: 'inward.transfer',
            domain:  [['state', '=', 'approve']],
            views: [[false, 'list'], [false, 'form']],
            target: 'current'
        });
    }

    view_production_summary(ev) {
        return this.actionService.doAction({
            name:'Production Summary',
            type: 'ir.actions.act_window',
            res_model: 'production.summary',
            domain: [['state', '=', 'approve']],
            views: [[false, 'list'], [false, 'form']],
            target: 'current'
        });
    }


    view_scrap(ev) {
        return this.actionService.doAction({
            name:'Scrap',
            type: 'ir.actions.act_window',
            res_model: 'stock.scrap',
            domain: [['state', '=', 'done'],['hatchery_poultry_id', '!=', false]],
            views: [[false, 'list'], [false, 'form']],
            target: 'current'
        });
    }


    view_cost_estimation(ev) {
        return this.actionService.doAction({
            name:'Cost Estimation',
            type: 'ir.actions.act_window',
            res_model: 'hen.cost.estimation',
            // domain: [['state', '=', 'approve']],
            views: [[false, 'list'], [false, 'form']],
            target: 'current'
        });
    }

    view_hen_veterinary(ev) {
        return this.actionService.doAction({
            name:'Appointments',
            type: 'ir.actions.act_window',
            res_model: 'hen.veterinary',
            domain: [['state', '=', 'draft']],
            views: [[false, 'list'], [false, 'form']],
            target: 'current'
        });
    }

    view_hatchery_picking(ev) {
        return this.actionService.doAction({
            name:'Hatchery Picking',
            type: 'ir.actions.act_window',
            res_model: 'stock.picking',
            domain: [['state', '=', 'done'],['hatchery_poultry_id', '!=', false]],
            views: [[false, 'list'], [false, 'form']],
            target: 'current'
        });
    }

    view_project(ev) {
        return this.actionService.doAction({
            name:'Project',
            type: 'ir.actions.act_window',
            res_model: 'project.project',
            domain: [['poultry', '!=', false]],
            views: [[false, 'list'], [false, 'form']],
            target: 'current'
        });
    }

    view_farm_house(ev) {
        return this.actionService.doAction({
            name:'Farm House',
            type: 'ir.actions.act_window',
            res_model: 'chicken.farm',
            domain: [['states', '=', 'approve']],
            views: [[false, 'list'], [false, 'form']],
            target: 'current'
        });
    }

    view_inward_farm_house(ev) {
        return this.actionService.doAction({
            name:'Inward Farm House',
            type: 'ir.actions.act_window',
            res_model: 'chicken.house',
            domain: [['production_type', '=', 'normal']],
            views: [[false, 'list'], [false, 'form']],
            target: 'current'
        });
    }

    view_prodcution_farm_house(ev) {
        return this.actionService.doAction({
            name:'Prodcution Farm House',
            type: 'ir.actions.act_window',
            res_model: 'chicken.house',
            domain: [['production_type', '=', 'production']],
            views: [[false, 'list'], [false, 'form']],
            target: 'current'
        });
    }

    view_main_product(ev) {
        return this.actionService.doAction({
            name:'Main product',
            type: 'ir.actions.act_window',
            res_model: 'product.product',
            domain: [['is_chicken', '=', true]],
            views: [[false, 'list'], [false, 'form']],
            target: 'current'
        });
    }

    view_final_product(ev) {
        return this.actionService.doAction({
            name:'Final product',
            type: 'ir.actions.act_window',
            res_model: 'product.product',
            domain: [['last_product', '=', true]],
            views: [[false, 'list'], [false, 'form']],
            target: 'current'
        });
    }

    view_bill(ev) {
        return this.actionService.doAction({
            name:'Bills',
            type: 'ir.actions.act_window',
            res_model: 'account.move',
            domain: [['move_type', '=', 'in_invoice']],
            views: [[false, 'list'], [false, 'form']],
            target: 'current'
        });
    }

    view_labour_sheets(ev) {
        return this.actionService.doAction({
            name:'Labour Sheets',
            type: 'ir.actions.act_window',
            res_model: 'account.analytic.line',
            // domain: [['move_type', '=', 'in_invoice']],
            views: [[false, 'list'], [false, 'form']],
            target: 'current'
        });
    }

    view_hr_employee(ev) {
        return this.actionService.doAction({
            name:'Employees',
            type: 'ir.actions.act_window',
            res_model: 'hr.employee',
            // domain: [['move_type', '=', 'in_invoice']],
            views: [[false, 'list'], [false, 'form']],
            target: 'current'
        });
    }

    view_project_task(ev) {
        return this.actionService.doAction({
            name:'Worke Orders',
            type: 'ir.actions.act_window',
            res_model: 'project.task',
            // domain: [['move_type', '=', 'in_invoice']],
            views: [[false, 'list'], [false, 'form']],
            target: 'current'
        });
    }


    try() {
        var self = this;
        rpc('/animal/dashboard', {}).then((result) => {
            this.AnimalDashboard = result;
            // Load Google Charts
            google.charts.load('current', {
                'packages': ['corechart']
            });
            google.charts.setOnLoadCallback(() => {
                if (document.getElementById('mygraph')) {
                    drawDonutChart();
                } else {
                    console.error('Chart containers not found');
                }
            });

            function drawDonutChart() {
                try {
                    // Death
                    var columnData = google.visualization.arrayToDataTable(result['death_monthly_data']);
                    var columnOptions = {
                        backgroundColor: 'transparent',
                        legend: 'none',
                        bar: { groupWidth: "40%" },
                    };
                    var charts = new google.visualization.ColumnChart(document.getElementById('mygraph'));
                    charts.draw(columnData, columnOptions);

                    // production summary
                    var column_data_2 = google.visualization.arrayToDataTable(result['production_monthly_data']);
                    var column_options_2 = {
                        'backgroundColor': 'transparent',
                        legend: 'none',
                        bar: {
                            groupWidth: "40%"
                        },
                    };
                    var charts_2 = new google.visualization.ColumnChart(document.getElementById('mygraph_2'));
                    charts_2.draw(column_data_2, column_options_2);

                    //Inward
                    var column_data_3 = google.visualization.arrayToDataTable(result['inward_monthly_data']);
                    var column_options_3 = {
                        'backgroundColor': 'transparent',
                        legend: 'none',
                        bar: {
                            groupWidth: "40%"
                        },
                    };
                    var charts_3 = new google.visualization.ColumnChart(document.getElementById('mygraph_3'));
                    charts_3.draw(column_data_3, column_options_3);

                    //Expenses
                    var column_data_4 = google.visualization.arrayToDataTable(result['expenses_monthly_data']);
                    var column_options_4 = {
                        'backgroundColor': 'transparent',
                        legend: 'none',
                        bar: {
                            groupWidth: "40%"
                        },
                    };
                    var charts_4 = new google.visualization.ColumnChart(document.getElementById('mygraph_4'));
                    charts_4.draw(column_data_4, column_options_4);
                    

                    var column_data_5 = google.visualization.arrayToDataTable(result['final_production_monthly_data']);
                    var column_options_5 = {
                        'backgroundColor': 'transparent',
                        legend: 'none',
                        bar: {
                            groupWidth: "40%"
                        },
                    };
                    var charts_5 = new google.visualization.ColumnChart(document.getElementById('mygraph_5'));
                    charts_5.draw(column_data_5, column_options_5);

                } catch (e) {
                    console.error("Error drawing charts:", e);
                }
            }
        });
    }
}
PoultryDashboard.template = "PoultryDashboard";
registry.category("actions").add("poultry_dashboard", PoultryDashboard);
