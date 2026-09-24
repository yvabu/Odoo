from odoo import models,fields,api
from odoo.exceptions import ValidationError


class HotelReservationLine(models.Model):
    _name='hotel.reservation.line'
    _description='Hotel Reservation Line'

    reservation_id=fields.Many2one('hotel.reservation', string="Reservation", required=True, ondelete='cascade')
    service_id=fields.Many2one('hotel.service',string='Service',required=True)
    quantity=fields.Integer(string="Quantity",default='1',required=True)
    price_unit=fields.Float(string="Unit Price")
    price_subtotal=fields.Float(string="Subtotal",compute='_compute_price_subtotal')
    invoiced=fields.Boolean(string="ინვოისში გატარებულია",default=False,readonly=True,copy=False,
        help="აღნიშნავს რომ ეს სერვის-ხაზი უკვე შესულია რომელიმე ინვოისში (Check-in-ის ან Check-out-ის დროს "
             "შექმნილში). ეხმარება სისტემას, არ დააინვოისოს ერთი და იგივე სერვისი ორჯერ.")

    @api.onchange('service_id')
    def _onchange_service_id(self):
        if self.service_id:
            self.price_unit=self.service_id.price

    @api.depends('quantity','price_unit')
    def _compute_price_subtotal(self):
        for rec in self:
            rec.price_subtotal=(rec.quantity *rec.price_unit)

    @api.constrains('quantity')
    def _check_quantity(self):
        for rec in self:
            if rec.quantity <= 0:
                raise ValidationError('რაოდენობა უნდა იყოს 0-ზე მეტი.')
    @api.constrains('price_unit')
    def _check_price_unit(self):
        for rec in self:
            if rec.price_unit <0:
                raise ValidationError('ფასი არ უნდა იყოს უარყოფითი რიცხვი')