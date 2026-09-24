from odoo import models, fields, api


class HotelEmployees(models.Model):
    _name = 'hotel.employee'
    _description = 'Hotel Employee'

    name = fields.Char(string='თანამშრომლის სახელი', required=True)
    surname=fields.Char(string="თანამშრომლის გვარი",required=True)
    email = fields.Char(string='ელექტრონული ფოსტა', required=True,compute='_compute_email')
    password = fields.Char(string="შეიყვანეთ თქვენთვის სასურველი პაროლი", required=True)
    phone = fields.Char(string='ტელეფონის ნომერი')
    role = fields.Selection([
        ('manager', 'Manager'),
        ('receptionist', 'Receptionist')
    ], string='როლი', required=True, default='receptionist')
    user_id=fields.Many2one('res.users',string='User',readonly=True)

    @api.depends('name','surname')
    def _compute_email(self):
        for rec in self:
            rec.email=f'{rec.name}.{rec.surname}@hotel.ge'



    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)


        for rec in records:
            if not rec.user_id:
                if rec.role == 'manager':
                    group = self.env.ref('hotel_erp.group_hotel_manager')
                else:
                    group = self.env.ref('hotel_erp.group_hotel_user')  # დარწმუნდი რომ XML ID სწორია



                user = self.env['res.users'].sudo().create({
                    'name': rec.name,
                    'email': rec.email,
                    'login': rec.email,
                    'password': rec.password,
                    'groups_id': [(4,group.id),
                                  (4,self.env.ref('base.group_user').id)]
                })
                rec.user_id = user.id

        return records