# -*- coding: utf-8 -*-
from odoo import fields, models


class HrEmployeePrivate(models.Model):
    _inherit = 'hr.employee'

    employee_location_id = fields.Many2one('stock.location',
                                         string="Destination Location",
                                         help='Employee location for inventory requisitions')