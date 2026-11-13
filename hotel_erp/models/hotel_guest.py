from odoo import models,fields,api
from odoo.exceptions import ValidationError


class HotelGuest(models.Model):
    _name='hotel.guest'
    _description='Hotel Guest'
    _inherit=['mail.thread','mail.activity.mixin']
    _sql_constraints=[(
        'unique_personal_number',
        'unique(personal_number)',
        'The personal number must be unique.!!!'
    ) ]

    name=fields.Char(string="Full Name",required=True)
    personal_number=fields.Char(string="Personal Number",required=True)
    phone=fields.Char(string="Phone Number" )
    email=fields.Char(string="Email")
    address=fields.Text(string='Address')
    active=fields.Boolean(string="active",default=True)
    reservation_count=fields.Integer(string='Number of reservations',compute="_compute_reservation_count")
    reservation_ids=fields.One2many('hotel.reservation','guest_id',string="Reservations")
    partner_id=fields.Many2one('res.partner',string="Contact",ondelete='restrict',readonly=True)
    user_id=fields.Many2one('res.users',string="Portal User",ondelete='set null',readonly=True)





    @api.constrains('personal_number')
    def _check_personal_number(self):
        for rec in self:
            if rec.personal_number:
                if len(rec.personal_number) !=11 or not rec.personal_number.isdigit():
                    raise ValidationError('The personal number must consist of 11 digits and must not contain any symbols.')
                if self.search([('personal_number','=',rec.personal_number),('id','!=',rec.id)]):
                    raise ValidationError('A user with this personal number already exists.')


    @api.constrains('email','phone')
    def _check_email_and_phone(self):
        for rec in self:
            if rec.email:
                if '@' not in rec.email or '.' not in rec.email:
                    raise ValidationError('The email must contain an @ symbol and a dot.')
            if rec.phone:
                if len(rec.phone) !=9 or not rec.phone.isdigit():
                    raise ValidationError('The mobile phone number must contain 9 digits; the use of symbols is not permitted.')

    def _compute_reservation_count(self):
        for rec in self:
            javshmis_raodenoba= self.env['hotel.reservation'].search_count([('guest_id','=',rec.id)])
            rec.reservation_count=javshmis_raodenoba

    def action_view_reservation(self):
        self.ensure_one()
        return{
            'name': 'Guest Reservation',
            'type': 'ir.actions.act_window',
            'res_model': 'hotel.reservation',
            'view_mode': 'list,form',
            'domain':  [('guest_id','=',self.id)],
            'context': {'default_guest_id':self.id}
        }


@api.model_create_multi
def create(self, vals_list):
    guests = super().create(vals_list)

    for guest in guests:
        if not guest.partner_id:
            partner = self.env['res.partner'].sudo().create({
                'name': guest.name,
                'phone': guest.phone,
                'email': guest.email,
            })
            guest.partner_id = partner.id

        if guest.email and not guest.user_id:
            existing_user = self.env['res.users'].sudo().search([('login', '=', guest.email)], limit=1)

            if not existing_user:
                portal_group = self.env.ref('base.group_portal')
                user = self.env['res.users'].sudo().create({
                    'name': guest.name,
                    'login': guest.email,
                    'email': guest.email,
                    'partner_id': guest.partner_id.id,
                    'groups_id': [(6, 0, [portal_group.id])],
                })
                guest.user_id = user.id
            else:
                guest.user_id = existing_user.id
                user = existing_user

            user.action_reset_password()

    return guests