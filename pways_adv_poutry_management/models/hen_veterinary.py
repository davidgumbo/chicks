from odoo import api, models, fields, _
from datetime import datetime,date
from odoo.exceptions import UserError, ValidationError

class HenVeterinary(models.Model):
    _name = "hen.veterinary"
    _description = "Hen Veterinary"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "name"
    _order = "id DESC"

    name = fields.Char('Name', copy=False, default=lambda self: _('New'), required=True)
    farm_house_id = fields.Many2one('chicken.house')
    lot_id = fields.Many2one('stock.lot')
    hen_treatment_ids = fields.One2many('hen.treatment', 'appointment_id')
    hen_vaccination_ids = fields.One2many('hen.vaccination', 'appointment_id')
    hen_gender = fields.Selection(selection=[
        ('male', 'Male'),
        ('female', 'Female')], string="Gender", required=True)
    behaviour = fields.Selection(selection=[
        ('treatment', 'Treatment'),
        ('vaccination', 'Vaccination')], string="Behaviour", required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('treatment', 'Treatment'),
        ('vaccination', 'Vaccination')], default="draft", copy=False)
    doctor_name = fields.Char(string="Doctor Name", required=True)
    phone = fields.Char(string="Phone", required=True)
    appointment_date = fields.Datetime(string="Date", default=datetime.today())
    address = fields.Char(string="Address", required=True)
    note = fields.Html(string="Note")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)

    
    @api.model
    def create(self, vals):
        if 'name' not in vals or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('hen.veterinary') or _('New')
        return super(HenVeterinary, self).create(vals)

    def button_draft(self):
        self.state = "draft"
        
    def create_treatment(self):
        treatment_obj = self.env['hen.treatment']
        vals = {
            'appointment_id': self.id,
            'farm_house_id' : self.farm_house_id.id,
            'lot_id' : self.lot_id.id,
        }
        treatment = treatment_obj.create(vals)
        self.state = 'treatment'
        action = {
            'type': 'ir.actions.act_window',
            'res_model': 'hen.treatment',
            'views': [(False, 'form')],
            'target': 'current',
            'res_id': treatment.id,
            }
        return action 

    def create_vaccination(self):
        vaccination_obj = self.env['hen.vaccination']
        vals = {
            'appointment_id': self.id,
            'farm_house_id' : self.farm_house_id.id,
            'lot_id' : self.lot_id.id,
        }
        vaccination = vaccination_obj.create(vals)
        self.state = 'vaccination'
        action = {
            'type': 'ir.actions.act_window',
            'res_model': 'hen.treatment',
            'views': [(False, 'form')],
            'target': 'current',
            'res_id': vaccination.id,
            }
        return action

class HenTreatment(models.Model):
    _name = "hen.treatment"
    _description = "Hen Treatment"
    _rec_name = "name"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', copy=False, default=lambda self: _('New'), required=True)
    farm_house_id = fields.Many2one('chicken.house')
    lot_id = fields.Many2one('stock.lot')
    hen_veterinary_id =  fields.Many2one('hen.veterinary')
    appointment_id = fields.Many2one('hen.veterinary')
    treatment = fields.Char(string="Treatment")
    treatment_line_ids = fields.One2many('hen.treatment.lines', 'hen_treatment_lines')
    description = fields.Text(string="Allergy Description")
    bill_count = fields.Integer(compute="_compute_bill_count")
    total_amount = fields.Float(string="Total", compute='_total_amount_all')
    start_date = fields.Date(string="Treatment Start")
    end_date = fields.Date(string="Treatment End")
    diseases = fields.Char(string="Diseases")
    state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted')], default="draft")
    allergy = fields.Selection(selection=[('yes', 'Yes'), ('no', 'No')], string="Allergy")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    

    @api.depends('treatment_line_ids.price__subtotal')
    def _total_amount_all(self):
        amount_total = 0
        for line in self:
            amount_total = sum(line.treatment_line_ids.mapped('price__subtotal'))
            line.total_amount = amount_total 

    def _compute_bill_count(self):
        for bill in self:
            bill.bill_count = self.env['account.move'].search_count([('treatment_id','=', self.id)])

    @api.model
    def create(self, vals):
        if 'name' not in vals or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('hen.treatment') or _('New')
        return super(HenTreatment, self).create(vals)

    def action_create_hen_bill(self):
        if not self.treatment_line_ids:
            raise ValidationError(_('You should have some product lines'))
        journal_id = self.env['account.journal'].search([('type', '=', 'purchase')], limit=1)
        move_type = 'in_invoice'
        bill_objs = self.env['account.move']
        for treatment in self:
            vals = {
                'treatment_id': treatment.id,
                'invoice_line_ids': treatment._prepare_account_move_line(),
                'journal_id': journal_id.id,
                'move_type': move_type,
                'is_farm_dairy' : True, 
                }
            bill_objs = self.env['account.move'].create(vals)
            self.state = 'posted'
        return bill_objs

    def action_open_bill(self):
        invoice_ids = self.env['account.move'].search([('treatment_id', '=', self.id)])
        return {
            'name': _('Create Bills'),
            'view_type': 'form',
            'view_mode': 'list,form',
            'view_id': False,
            'res_model': 'account.move',
            'context': "{}",
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', invoice_ids.ids)],
        }       

    def _prepare_account_move_line(self, move=False):
        res_list = []
        for rec in self.treatment_line_ids:
            res = {
                'product_id': rec.product_id.id,
                'quantity': rec.quantity,
                'price_unit': rec.price_unit,
                'lot_ids': [(4, self.lot_id.id)] if self.lot_id else [],
            }
            res_list.append((0, 0, res))
        return res_list

class HenTreatmentLines(models.Model):
    _name = "hen.treatment.lines"

    hen_treatment_lines = fields.Many2one('hen.treatment')
    precautions = fields.Char(string="Precautions", required=True)
    product_id = fields.Many2one(comodel_name='product.product',string='Medicine Name')
    quantity = fields.Float(string='Quantity', default=1.0)
    price_unit = fields.Float(string="Price", related="product_id.lst_price")
    price__subtotal = fields.Float(string='Subtotal', compute='_compute_totals', store=True,)

    @api.depends('product_id', 'quantity', 'price_unit')
    def _compute_totals(self):
        for rec in self:
            rec.price__subtotal = rec.quantity * rec.price_unit


class HenVaccination(models.Model):
    _name = "hen.vaccination"
    _description = "Hen Vaccination"
    _rec_name = "name"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', copy=False, default=lambda self: _('New'), required=True)
    farm_house_id = fields.Many2one('chicken.house')
    lot_id = fields.Many2one('stock.lot')
    hen_veterinary_id = fields.Many2one('hen.veterinary')
    state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted')], default="draft")
    bill_count = fields.Integer(compute="_compute_bill_count")
    vaccination_line_ids = fields.One2many('hen.vaccination.lines', 'hen_vaccination_lines')
    appointment_id = fields.Many2one('hen.veterinary')
    total_amount = fields.Float(string="Total", compute='_total_amount_all')
    vaccination_name = fields.Char(string="Vaccine")
    vaccination_date = fields.Date(string="Vaccination Date")
    exp_date = fields.Date(string="Expiry Date")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    
    @api.depends('vaccination_line_ids.price__subtotal')
    def _total_amount_all(self):
        amount_total = 0
        for line in self:
            amount_total = sum(line.vaccination_line_ids.mapped('price__subtotal'))
            line.total_amount = amount_total

    @api.model
    def create(self, vals):
        if 'name' not in vals or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('hen.vaccination') or _('New')
        return super(HenVaccination, self).create(vals)
    
    def _compute_bill_count(self):
        for bill in self:
            bill.bill_count = self.env['account.move'].search_count([('vaccination_id','=', self.id)])

    def action_open_vaccination_bill(self):
        invoice_ids = self.env['account.move'].search([('vaccination_id', '=', self.id)])
        return {
            'name': _('Create Bills'),
            'view_type': 'form',
            'view_mode': 'list,form',
            'view_id': False,
            'res_model': 'account.move',
            'context': "{}",
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', invoice_ids.ids)],
        }   

    def action_create_vaccination_bill(self):
        if not self.vaccination_line_ids:
            raise ValidationError(_('You should have some product lines'))
        journal_id = self.env['account.journal'].search(domain=[('type', '=', 'purchase')], limit=1,)
        move_type = 'in_invoice'
        bill_objs = self.env['account.move']
        for vaccination in self:
            vals = {
                'vaccination_id': vaccination.id,
                'partner_id':  vaccination.hen_veterinary_id.id,
                'invoice_line_ids': vaccination._prepare_account_move_line(),
                'journal_id': journal_id.id ,
                'move_type': move_type,
                'is_farm_dairy' : True,
            }
            bill_objs =  self.env['account.move'].create(vals)
            self.state = 'posted'
        return bill_objs
    
    def _prepare_account_move_line(self, move=False):
        res_list = []
        for rec in self.vaccination_line_ids:
            res = {
                'product_id': rec.product_id.id,
                'quantity': rec.quantity,
                'price_unit': rec.price_unit,
                'lot_ids': [(4, self.lot_id.id)] if self.lot_id else [],
            }
            res_list.append((0, 0, res))
        return res_list 

class HenVaccinationLines(models.Model):
    _name = "hen.vaccination.lines"

    hen_vaccination_lines = fields.Many2one('hen.vaccination')
    description = fields.Char(string="Description")
    product_id = fields.Many2one(comodel_name='product.product',string='Vaccine Name')
    quantity = fields.Float(string='Quantity', default=1.0)
    price_unit = fields.Float(string="Price", related="product_id.lst_price")
    price__subtotal = fields.Float(string='Subtotal', compute='_compute_totals', store=True,)

    @api.depends('product_id', 'quantity', 'price_unit')
    def _compute_totals(self):
        for rec in self:
            rec.price__subtotal = rec.quantity * rec.price_unit

