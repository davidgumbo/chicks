# -*- coding: utf-8 -*-
from odoo import fields, models


class Department(models.Model):
    _inherit = 'hr.department'

    department_location_id = fields.Many2one('stock.location',
                                           string='Source Location',
                                           help='Department location for inventory requisitions')