from odoo import fields,models
from odoo.exceptions import ValidationError

class Cancelwizard(models.TransientModel):
    _name= 'hotel.reservation.cancel.wizard'
    _description = 'Hotel Reservation Cancel Wizard'

    reservation_id = fields.Many2one('hotel.reservation',string='Reservation',required=True,readonly=True)
    reason=fields.Text(string='Reason for cancellation',required=True)
    currency_id=fields.Many2one(related='reservation_id.currency_id',readonly=True)
    paid_amount=fields.Monetary(related='reservation_id.paid_amount',currency_field='currency_id')


    def action_confirm_cancel(self):
        self.ensure_one()
        if self.reason.strip()== '':
            raise ValidationError('Please enter the reason for cancellation; this is a mandatory field, and the operation cannot be completed without it.')
        self.reservation_id.action_cancel(reason=self.reason)
        return {
            'type': 'ir.actions.act_window_close',
        }