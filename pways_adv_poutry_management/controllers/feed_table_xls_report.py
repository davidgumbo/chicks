from odoo import http
from odoo.http import content_disposition, request
import io
import xlsxwriter

class VoucherxlsReport(http.Controller):
    @http.route(['/project/feed_table_xls_report/<int:active_id>'], type='http', auth="user", csrf=False)
    def get_feed_table_xls_rprt(self, active_id=None, **args):
        # Fetch the feed table data based on active_id
        feed_table = request.env['feed.table'].browse(active_id)
        
        # Prepare HTTP response
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', content_disposition('Feed_Table_Report.xlsx'))
            ]
        )
        
        # Create an in-memory output for the workbook
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        # Define formats for the cells
        header_format = workbook.add_format({'bold': True, 'align': 'center', 'font_name': 'Times New Roman'})
        shift_header_format = workbook.add_format({'bold': True, 'font_color': 'blue', 'align': 'center', 'font_name': 'Times New Roman'})
        line_header_format = workbook.add_format({'bold': True, 'font_color': 'black', 'align': 'center', 'font_name': 'Times New Roman'})
        data_format = workbook.add_format({'align': 'center', 'font_name': 'Times New Roman'})
        
        # Map of weekday selections to labels
        days = {
            '0': 'Monday', '1': 'Tuesday', '2': 'Wednesday',
            '3': 'Thursday', '4': 'Friday', '5': 'Saturday', '6': 'Sunday'
        }
        
        # Shift mapping
        shifts = {
            'morning': 'Morning Shift', 
            'evening': 'Evening Shift', 
            'night': 'Night Shift'
        }
        
        # Loop through each day to create a new sheet with data
        for day_code, day_name in days.items():
            # Create a new sheet for each day
            sheet = workbook.add_worksheet(day_name)
            # sheet.write(0, 0, 'Feed Table Line', line_header_format)
            sheet.write(0, 1, 'Product', header_format)
            sheet.write(0, 2, 'Quantity', header_format)
            sheet.write(0, 3, 'UoM', header_format)
            
            row = 1  # Start data from the second row

            # Filter lines by day of the week and loop through each shift
            for shift_code, shift_name in shifts.items():
                # Write the shift header
                sheet.merge_range(row, 0, row, 3, shift_name, shift_header_format)
                row += 1

                # Filter lines by shift and day
                feed_lines = feed_table.feed_table_line_ids.filtered(
                    lambda l: l.dayofweek == day_code and l.shift == shift_code
                )

                for feed_line in feed_lines:
                    # Print Feed Table Line name
                    # sheet.write(row, 0, feed_line.name, line_header_format)

                    # Print each product under the Feed Table Line
                    for product_line in feed_line.feed_table_product_line_ids:
                        sheet.write(row, 1, product_line.product_id.name or '', data_format)
                        sheet.write(row, 2, product_line.qty or 0, data_format)
                        sheet.write(row, 3, product_line.uom_id.name or '', data_format)
                        row += 1

                    # row += 1  # Add a blank row after each Feed Table Line group
                
                row += 1  # Add spacing between shifts

            # Optional: Adjust column width for readability
            sheet.set_column('A:D', 20)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

        return response
