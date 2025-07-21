# -*- coding: utf-8 -*-
from odoo import fields, models


class Picking(models.Model):
    _inherit = 'stock.picking'

    requisition_order = fields.Char(string='Requisition Order',
                                  help='Requisition order sequence')