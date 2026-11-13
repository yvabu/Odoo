from odoo import models,fields,api
from odoo.exceptions import ValidationError
class HotelRoom(models.Model):
    _name='hotel.room'
    _description='Hotel Room'
    _rec_name='room_number'

    room_number=fields.Char(string="Room Number",required=True,default='#',copy=False)
    room_type=fields.Selection([('single','Single'),('double','Double',),('vip','VIP')],string='ოთახის ტიპი',required=True)
    currency_id=fields.Many2one('res.currency', string='Currency',default=lambda self:self.env.company.currency_id ,readonly=True)
    room_price=fields.Monetary(string='Room Price For One Night',currency_field='currency_id',required=True)
    room_status=fields.Selection(
        [
          ('available','Available'),
          ('occupied','Occupied'),
          ('maintenance','Maintenance'),
          ('inactive','Inactive'),
        ],
        string='Status',
        default='available'
    )
    floor=fields.Integer(string='Floor')
    capacity=fields.Integer(string='Room capacity',required=True,default=1)
    description=fields.Text(string='Description')
    active=fields.Boolean(default=True)
    is_wifi=fields.Boolean(string="WI-FI")
    is_air_conditioning=fields.Boolean(string='Air Conditioning')
    balcony_count=fields.Integer(string='Balcony Count',default=1)
    is_smoking=fields.Boolean(string='Smoking Allowed')
    image_1920=fields.Image(string='Main image',max_width=1920,max_height=1920)
    image_ids=fields.One2many('hotel.room.images','room_id',string="Gallery")
    reservation_ids=fields.One2many('hotel.reservation','room_id',string="Reservations")
    reservation_count=fields.Integer(string="Number of reservations",compute="_compute_reservation_count")
    housekeeping_status=fields.Selection([('clean','Clean'),('dirty','Dirty'),('cleaning','Cleaning')],default='clean',required=True)
    is_occupied_now=fields.Boolean(string='Occupied',compute='_compute_occupied_now')


    @api.depends('reservation_ids.state')
    def _compute_occupied_now(self):
        for rec in self:
            rec.is_occupied_now=any(r.state=='checked_in' for r in rec.reservation_ids)

    @api.constrains('room_price')
    def _check_room_price(self):
        for rec in self:
            if rec.room_price <=0:
                raise ValidationError('The price cannot be zero or less than zero.')

    @api.constrains('room_type','capacity')
    def _check_room_type(self):
        for rec in self:
            if rec.room_type:
                if rec.room_type=='single' and rec.capacity >1:
                    raise ValidationError('In a single-type room, the number of men must be equal to 1.')
                if rec.room_type=='double' and rec.capacity>2:
                    raise ValidationError('The number of people in a double room should be equal to 2')
    @api.constrains('capacity')
    def _check_capacity(self):
        for rec in self:
            if rec.capacity<=0:
                raise ValidationError('The count cannot be 0 or less than 0')
    @api.constrains('room_number')
    def _check_room_number(self):
        for rec in self:
            if rec.room_number:
                if self.search([('room_number','=',rec.room_number),('id','!=',rec.id)]):
                    raise ValidationError('A room with this name already exists!')


    def action_set_clean(self):
        for rec in self:
            if rec.housekeeping_status!='cleaning':
                raise ValidationError('A room can be set to "Clean" only after the cleaning process has been completed.')
            rec.housekeeping_status='clean'

    def action_set_dirty(self):
        for rec in self:
            if rec.housekeeping_status=='dirty':
                continue
            rec.housekeeping_status='dirty'

    def action_set_cleaning(self):
        for rec in self:
            if rec.housekeeping_status !='dirty':
                raise ValidationError('Cleaning can be started only for a "Dirty" room.')
            rec.housekeeping_status='cleaning'


    def action_set_maintenance(self):
        for rec in self:
            if rec.is_occupied_now:
                raise ValidationError('The room is busy, it cannot be transferred to maintenance')
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

    def action_set_inactive(self):
        for rec in self:
            if rec.is_occupied_now:
                raise ValidationError('The room is occupied; it cannot be set to Inactive.')
            rec.room_status='inactive'

    def action_set_available(self):
        self.ensure_one()
        if self.room_status not in ('maintenance','inactive'):
            raise ValidationError('Transition to "Available" is possible only from "Maintenance" or "Inactive" states.')
        self.write({'room_status':'available'})

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