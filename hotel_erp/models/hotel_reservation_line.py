from email.policy import default

from odoo import models,fields,api
from odoo.exceptions import ValidationError


class HotelReservationLine(models.Model):
    _name='hotel.reservation.line'
    _description='Hotel Reservation Line'

    reservation_id=fields.Many2one('hotel.reservation', string="Reservation", required=True, ondelete='cascade')
    service_id=fields.Many2one('hotel.service',string='Service',required=True)
    quantity=fields.Integer(string="Quantity",default='1',required=True)
    currency_id=fields.Many2one('res.currency', string='Currency',default=lambda self:self.env['res.currency'].search([('name','=','GEL')],limit=1) ,readonly=True)
    price_unit=fields.Monetary(string="Unit Price",currency_field='currency_id')
    price_subtotal=fields.Monetary(string="Subtotal",currency_field='currency_id',compute='_compute_price_subtotal')
    invoiced=fields.Boolean(string="Recorded in the invoice",default=False,readonly=True,copy=False,
        help="Indicates that this service line item is already included in an invoice (created during check-in or check-out). This helps the system avoid invoicing the same service twice.")



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
                raise ValidationError('The count must be greater than 0.')
    @api.constrains('price_unit')
    def _check_price_unit(self):
        for rec in self:
            if rec.price_unit <0:
                raise ValidationError('The price must not be a negative number.')