from odoo import models,fields,api
from odoo.exceptions import ValidationError


class HotelGuest(models.Model):
    _name='hotel.guest'
    _description='Hotel Guest'
    _inherit=['mail.thread','mail.activity.mixin']
    _sql_constraints=[(
        'unique_personal_number',
        'unique(personal_number)',
        'პირადი ნომერი უნდა იყოს უნიკალური!!!'
    ) ]

    name=fields.Char(string="Full Name",required=True)
    personal_number=fields.Char(string="Personal Number",required=True)
    phone=fields.Char(string="Phone Number" )
    email=fields.Char(string="Email")
    address=fields.Text(string='Address')
    active=fields.Boolean(string="active",default=True)
    reservation_count=fields.Integer(string='ჯავშანთა რაოდენობა',compute="_compute_reservation_count")
    reservation_ids=fields.One2many('hotel.reservation','guest_id',string="Reservations")
    partner_id=fields.Many2one('res.partner',string="Contact",ondelete='restrict',readonly=True)
    user_id=fields.Many2one('res.users',string="Portal User",ondelete='set null',readonly=True)





    @api.constrains('personal_number')
    def _check_personal_number(self):
        for rec in self:
            if rec.personal_number:
                if len(rec.personal_number) !=11 or not rec.personal_number.isdigit():
                    raise ValidationError('პირადი ნომერი უნდა შედგებოდეს 11 ციფრისაგან და არ უნდა შეიცავდეს სიმბოლოებს')
                if self.search([('personal_number','=',rec.personal_number),('id','!=',rec.id)]):
                    raise ValidationError('ასეთი პირადი ნომრით უკვე არსებობს მომხამრებელი')


    @api.constrains('email','phone')
    def _check_email_and_phone(self):
        for rec in self:
            if rec.email:
                if '@' not in rec.email or '.' not in rec.email:
                    raise ValidationError('ემაილი უნდა შეიცავდეს @-სა და .-ილს')
            if rec.phone:
                if len(rec.phone) !=9 or not rec.phone.isdigit():
                    raise ValidationError('მობილური ტელეფონის ნომერი უნდა შეიცავდეს 9 ციფრს,სიმბოლოების გამოყენება არ შეიძლება')

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
    def create(self,vals_list):
        for vals in vals_list:
            # 🔑 თუ partner_id უკვე გადმოცემულია (მაგ. საიტიდან ჯავშნის დროს, სადაც სტუმარს
            # უკვე შეექმნა res.partner + res.users ანგარიში), აღარ ვქმნით ახალს —
            # წინააღმდეგ შემთხვევაში ეს override ყოველთვის თავიდან ქმნიდა partner-ს და
            # კარგავდა კავშირს ახლადრეგისტრირებული user-ის ანგარიშთან.
            if not vals.get('partner_id'):
                partner=self.env['res.partner'].create({
                    'name':vals.get('name'),
                    'phone':vals.get('phone'),
                    'email':vals.get('email')
                })
                vals['partner_id']=partner.id
        return super().create(vals_list)
