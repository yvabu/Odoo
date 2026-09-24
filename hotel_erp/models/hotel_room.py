from email.policy import default

from odoo import models,fields,api
from odoo.exceptions import ValidationError


class HotelRoom(models.Model):
    _name='hotel.room'
    _description='Hotel Room'
    _rec_name='room_number'

    room_number=fields.Char(string="Room Number",required=True,default='#',copy=False)
    room_type=fields.Selection([('single','Single'),('double','Double',),('vip','VIP')],string='ოთახის ტიპი',required=True)
    room_price=fields.Float(string='Room Price For One Night',required=True)
    room_status=fields.Selection(
        [
          ('available','Available'),
          ('occupied','Occupied'),
          ('maintenance','Maintenance')
        ],
        string='Status',
        default='available'
    )
    floor=fields.Integer(string='Floor')
    capacity=fields.Integer(string='ოთახის ტევადობა',required=True,default=1)
    description=fields.Text(string='Description')
    active=fields.Boolean(default=True)
    is_wifi=fields.Boolean(string="WI-FI")
    is_air_conditioning=fields.Boolean(string='Air Conditioning')
    balcony_count=fields.Integer(string='Balcony Count',default=1)
    is_smoking=fields.Boolean(string='Smoking Allowed')
    image=fields.Image(string='image',max_width=1920,max_height=1920)
    reservation_ids=fields.One2many('hotel.reservation','room_id',string="Reservations")
    reservation_count=fields.Integer(string="ჯავშანთა რაოდენობა",compute="_compute_reservation_count")
    housekeeping_status=fields.Selection([('clean','Clean'),('dirty','Dirty'),('inspection','Needs Inspection')],default='clean',required=True)

    @api.constrains('room_price')
    def _check_room_price(self):
        for rec in self:
            if rec.room_price <=0:
                raise ValidationError('ფასი არ შეიძლება ნული ან მასზე ნაკლები იყოს')

    @api.constrains('room_type','capacity')
    def _check_room_type(self):
        for rec in self:
            if rec.room_type:
                if rec.room_type=='single' and rec.capacity >1:
                    raise ValidationError('Single ტიპის ოთახში კაცთა რაოდენობა უნდა უდრიდეს 1-ს')
                if rec.room_type=='double' and rec.capacity>2:
                    raise ValidationError('Double ტიპის ოთახში კაცთა რაოდენობა უნდა უდრიდეს 2-ს')
    @api.constrains('capacity')
    def _check_capacity(self):
        for rec in self:
            if rec.capacity<=0:
                raise ValidationError('რაოდენობა არ შეიძლება იყოს 0 ან 0-ზე ნაკლები')
    @api.constrains('room_number')
    def _check_room_number(self):
        for rec in self:
            if rec.room_number:
                if self.search([('room_number','=',rec.room_number),('id','!=',rec.id)]):
                    raise ValidationError('ამ სახელით ოთახი უკვე არსებობს!')


    def action_set_clean(self):
        for rec in self:
            rec.housekeeping_status='clean'
    def action_set_dirty(self):
        for rec in self:
            rec.housekeeping_status='dirty'

    def action_set_status_maintenance(self):
        for rec in self:
            rec.housekeeping_status='maintenance'
    def action_set_maintenance(self):
        for rec in self:
            if rec.room_status=='occupied':
                raise ValidationError('ოთახი დაკავებულია, მისი maintenance-ზე გადაყვანა შეუძლებელია')
            rec.room_status='maintenance'
    def _compute_reservation_count(self):
        for rec in self:
            javshnebi=self.env['hotel.reservation'].search_count([('room_id','=',rec.id)])
            rec.reservation_count=javshnebi

    def action_view_reservation(self):
        self.ensure_one()
        return{
            'name': 'Hotel Room Reservation',
            'type': 'ir.actions.act_window',
            'res_model': 'hotel.reservation',
            'view_mode': 'list,form,calendar',
            'domain':   [('room_id','=',self.id)],
            'context':  {'default_room_id':self.id}
        }

    def action_set_available(self):
        self.ensure_one()
        if self.room_status !='maintenance':
            raise ValidationError('მხოლოდ Maintenance მდგომარეობაში მყოფი ოთახის გადაყვანაა შესაძლებელი Available-ზე.')
        self.write({'room_status':'available'})

    def set_occupied(self):
        self.ensure_one()
        self.write({'room_status':'occupied'})
    def action_copy_room(self):
        self.ensure_one()
        self.copy(default={
            'room_number': f"{self.room_number}_COPY",
            'room_status': 'available'
        })
    def write(self,vals):
        if vals.get('room_price',0) <0:
            raise ValidationError("Room Price can not be negative")
        return super().write(vals)
    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            if vals.get('room_number','#')=='#':
                vals['room_number']=self.env['ir.sequence'].next_by_code('hotel.room')
        return super().create(vals_list)
    def get_available_rooms(self):
        rooms=self.search([('room_status','=','available'),('active','=',True),('housekeeping_status','=','clean')])
        return rooms