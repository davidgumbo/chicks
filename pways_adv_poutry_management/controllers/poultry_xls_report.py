from odoo import http
from odoo.http import content_disposition, request
import io
import xlsxwriter


class PoultryxlsReport(http.Controller):
    @http.route('/poultry/poultry_xls_report', type='http', auth="user")
    def get_poultry_xls_rprt(self, **kwargs):
        death_summary_records = request.env['death.summary'].search([])
        expense_records = request.env['account.move'].search([
            '|', '|', '|', '|', '|',
            ('hatchery_poultry_id', '!=', False),
            ('hen_expense_id', '!=', False),
            ('treatment_id', '!=', False),
            ('vaccination_id', '!=', False),
            ('hen_veterinary_id', '!=', False),
            ('is_farm_dairy', '=', True),
        ])
        Production_records = request.env['stock.picking'].search([('production_summary_id', '!=', False)])
        
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', content_disposition('Poultry XLS Report' + '.xlsx'))
            ]
        )
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        # Define styles
        title_style = workbook.add_format({'font_name': 'Times', 'font_size': 14, 'bold': True, 'align': 'center'})
        header_style = workbook.add_format({'font_name': 'Times', 'bold': True, 'align': 'center'})
        text_style = workbook.add_format({'font_name': 'Times', 'align': 'left'})

        # Sheet Names
        sheet_names = ['Batch In', 'Expense', 'Production', 'Batch Death']

        for sheet_name in sheet_names:
            sheet = workbook.add_worksheet(sheet_name)
            sheet.set_landscape()
            sheet.set_paper(9)
            sheet.set_margins(0.5, 0.5, 0.5, 0.5)

            
            sheet.merge_range('A2:F2', f'{sheet_name} Report', title_style)

            ############# Batch Death #################
            if sheet_name == 'Batch Death':
                # Group records by lot_id
                grouped_records = {}
                for record in death_summary_records:
                    lot_name = record.lot_id.name if record.lot_id else 'No Lot'
                    if lot_name not in grouped_records:
                        grouped_records[lot_name] = []
                    grouped_records[lot_name].append(record)

                # Write data
                row = 4
                for lot_name, records in grouped_records.items():
                    # Write Lot Name with "Batch No:" and merge columns
                    sheet.merge_range(row, 0, row, 4, f'Batch No: {lot_name}', title_style)
                    row += 1

                    # Write Headers
                    headers = ['Name', 'Date', 'Quantity', 'Summary', 'Farm House', 'Location']
                    for col_num, header in enumerate(headers):
                        sheet.write(row, col_num, header, header_style)
                    row += 1

                    # Write Values and Calculate Total Quantity
                    total_qty = 0
                    for record in records:
                        sheet.write(row, 0, record.name, text_style)  # Name
                        sheet.write(row, 1, record.date.strftime('%Y-%m-%d'))  # Date
                        qty = int(record.qty or 0)  # Safely convert qty to integer
                        sheet.write(row, 2, qty, text_style)  # Quantity
                        total_qty += qty  # Add to total
                        sheet.write(row, 3, record.summary, text_style)  # Summary
                        sheet.write(row, 4, record.normal_house_id.name)  # Farm Expense
                        sheet.write(row, 5, record.normal_house_id.location_id.name)  # Farm Expense
                        row += 1


                    # Write Total Quantity Row
                    sheet.merge_range(row, 0, row, 1, 'Total Quantity', header_style)
                    sheet.write(row, 2, total_qty, text_style)  # Write total in 'Quantity' column
                    row += 2  # Add an empty row after each lot group
             
            
            ############# Expense #################
            if sheet_name == 'Expense':
                # Group expense_records by lot (Many2many relationship)
                grouped_expense_lines = {}
                for record in expense_records:
                    for line in record.line_ids:
                        # Loop through each lot in the Many2many field
                        for lot in line.lot_ids:
                            lot_name = lot.name if lot else 'No Lot'
                            if lot_name not in grouped_expense_lines:
                                grouped_expense_lines[lot_name] = []
                            grouped_expense_lines[lot_name].append(line)

                # Write data
                row = 4
                for lot_name, lines in grouped_expense_lines.items():
                    # Write Lot Name with "Batch No:" and merge columns
                    sheet.merge_range(row, 0, row, 4, f'Lot: {lot_name}', title_style)
                    row += 1

                    # Write Headers
                    headers = ['Name', 'Date', 'Quantity', 'Price Unit', 'Subtotal']
                    for col_num, header in enumerate(headers):
                        sheet.write(row, col_num, header, header_style)
                    row += 1

                    # Write Values and Calculate Total
                    total_price_subtotal = 0
                    for line in lines:
                        sheet.write(row, 0, line.name, text_style)  # Name
                        sheet.write(row, 1, line.date.strftime('%Y-%m-%d') if line.date else '', text_style)  # Date
                        sheet.write(row, 2, line.quantity, text_style)  # Quantity
                        sheet.write(row, 3, line.price_unit, text_style)  # Price Unit
                        subtotal = line.price_subtotal or 0  # Ensure subtotal is numeric
                        sheet.write(row, 4, subtotal, text_style)  # Subtotal
                        total_price_subtotal += subtotal  # Add to total
                        row += 1

                    # Write Total Subtotal Row
                    sheet.merge_range(row, 0, row, 3, 'Total Subtotal', header_style)
                    sheet.write(row, 4, total_price_subtotal, text_style)  # Write total in 'Subtotal' column
                    row += 2  # Add an empty row after each lot group
            
            
            ############# Production #################
            if sheet_name == 'Production':

                grouped_product_lines = {}
                for record in Production_records:
                    for line in record.move_ids_without_package:
                        # Safely access lot_ids and group by lot name
                        for lot in line.lot_ids:
                            lot_name = lot.name if lot else 'No Lot'
                            grouped_product_lines.setdefault(lot_name, []).append(line)

                
                row = 4  # Starting row for writing data
                for lot_name, lines in grouped_product_lines.items():
                    # Write the Lot Name with "Lot:" prefix and merge columns
                    sheet.merge_range(row, 0, row, 4, f'Lot: {lot_name}', title_style)
                    row += 1

                    # Write Headers
                    headers = ['Product', 'Demand', 'Quantity', 'UOM']
                    for col_num, header in enumerate(headers):
                        sheet.write(row, col_num, header, header_style)
                    row += 1

                    # Write Line Details
                    total_quantity = 0
                    for line in lines:
                        sheet.write(row, 0, line.product_id.name if line.product_id else 'No Product', text_style)
                        sheet.write(row, 1, line.product_uom_qty or 0, text_style)  # Demand
                        qty = line.quantity or 0  # Default to 0 if None
                        sheet.write(row, 2, qty, text_style)  # Quantity
                        total_quantity += qty  # Add to total
                        sheet.write(row, 3, line.product_uom.name if line.product_uom.name else 'No UOM', text_style)
                        row += 1

                    # Write Total Row
                    sheet.merge_range(row, 0, row, 2, 'Total Quantity', header_style)
                    sheet.write(row, 3, total_quantity, text_style)  # Write total in 'Quantity' column
                    row += 2  # Add an empty row after each lot group

            
            ############# Batch In #################
            if sheet_name == 'Batch In':
                # Fetch incoming stock pickings (that are linked to purchase orders)
                batch_records = request.env['stock.picking'].search([('picking_type_id.code', '=', 'incoming')])

                # Group records by lot and filter by purchase order's farm_id (only those with farm_id)
                grouped_batch_lines = {}
                for record in batch_records:
                    # Check if the related purchase order has a farm_id
                    if record.purchase_id and record.purchase_id.farm_id:
                        for line in record.move_ids_without_package:  # Use move_ids_without_package for stock picking lines
                            for lot in line.lot_ids:  # Assuming lot_ids is a Many2many field on move line
                                lot_name = lot.name if lot else 'No Lot'
                                # Group by lot_name and store the line data
                                grouped_batch_lines.setdefault(lot_name, []).append(line)

                # Start writing data to the sheet
                row = 4
                for lot_name, lines in grouped_batch_lines.items():
                    sheet.merge_range(row, 0, row, 4, f'Lot: {lot_name}', title_style)
                    row += 1

                    # Write Headers
                    headers = ['Product', 'Demand', 'Quantity', 'UOM']
                    for col_num, header in enumerate(headers):
                        sheet.write(row, col_num, header, header_style)
                    row += 1

                    # Write Line Details
                    total_quantity = 0
                    for line in lines:
                        sheet.write(row, 0, line.product_id.name if line.product_id else 'No Product', text_style)
                        sheet.write(row, 1, line.product_uom_qty or 0, text_style)  # Use product_uom_qty for demand
                        qty = line.quantity or 0  # Use quantity for received quantity, default to 0 if None
                        sheet.write(row, 2, qty, text_style)
                        total_quantity += qty  # Accumulate total quantity
                        sheet.write(row, 3, line.product_uom.name if line.product_uom else 'No UOM', text_style)
                        row += 1

                    # Write Total Row for Quantity
                    sheet.merge_range(row, 0, row, 1, 'Total Quantity', header_style)
                    sheet.write(row, 2, total_quantity, text_style)  # Write total in 'Quantity' column
                    row += 3  # Add an empty row after each lot group

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

        return response