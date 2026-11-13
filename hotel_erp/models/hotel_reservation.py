import base64
from datetime import timedelta
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from markupsafe import escape
import logging

_logger=logging.getLogger(__name__)


class HotelReservation(models.Model):
    _name = 'hotel.reservation'
    _description = 'Hotel Reservation'

    name = fields.Char(string="Reservation Reference", default='New', required=True)
    guest_id = fields.Many2one('hotel.guest', string='Guest', required=True)
    room_id = fields.Many2one('hotel.room', string='Room', required=True)
    check_in = fields.Date(string="Check In", required=True)
    check_out = fields.Date(string="Check Out", required=True)
    currency_id = fields.Many2one('res.currency', string='Currency',default=lambda self: self.env.company.currency_id, readonly=True)
    room_price = fields.Monetary( currency_field='currency_id',string='Room price (1 night)', readonly=True, store=True)
    pending_date=fields.Datetime(string="Pending Date", readonly=True)
    hold_expires_at = fields.Datetime(string="Hold Expires At", readonly=True, copy=False)
    confirmed_at = fields.Datetime(string="Confirmed At", readonly=True, copy=False)
    confirmed_by = fields.Many2one('res.users', string="Confirmed By", readonly=True, copy=False)
    cancelled_at = fields.Datetime(string="Cancelled At", readonly=True, copy=False)
    cancellation_reason = fields.Text(string="Cancellation Reason",readonly=True, copy=False)
    checked_in_at = fields.Datetime(string="Checked In At", readonly=True, copy=False)
    checked_out_at = fields.Datetime(string="Checked Out At", readonly=True, copy=False)
    total_price = fields.Monetary(string="Total Price", currency_field='currency_id',compute="_compute_total_price", store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('checked_in', 'Checked In'),
        ('checked_out', 'Checked Out'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ], string='State', default="draft")

    service_line_ids = fields.One2many('hotel.reservation.line', 'reservation_id', string="Service Lines")
    invoice_id = fields.Many2one(
        'account.move', string="Room Invoice", readonly=True, copy=False,
        help="Invoice for room charges."
    )
    service_invoice_ids = fields.Many2many(
        'account.move', 'hotel_reservation_service_invoice_rel',
        'reservation_id', 'invoice_id', string="Service Invoices", readonly=True, copy=False,
        help="Invoices for additional services."
    )

    advance_payment_ids = fields.One2many(
        'account.payment', 'reservation_id',
        string="Advance payments / deposits", readonly=True
    )

    payment_ids = fields.Many2many('account.payment', string="Payments", compute="_compute_payment_ids", readonly=True)
    paid_amount = fields.Monetary(
        string="Paid Amount", currency_field='currency_id',
        compute="_compute_paid_amount_calculation", store=True
    )

    payment_status = fields.Selection(
        [('unpaid', 'Unpaid'), ('partial', 'Partially Paid'), ('paid', 'Paid'), ('overpaid', 'Overpaid'),],
        compute="_compute_payment_status", store=True
    )
    amount_due = fields.Monetary(
        string="Remaining balance", currency_field='currency_id',
        compute="_compute_amount_due", store=True
    )
    change_to_return = fields.Monetary(
        string="Change to be returned", currency_field='currency_id',
        compute='_compute_change_to_return'
    )
    active = fields.Boolean(string="Active", default=True)



    @api.model
    def _cron_auto_checkout(self):
        reservations=self.search([('state','=','checked_in'),('check_out','<=',fields.Date.today())])
        for rec in reservations:
            try:
                rec.action_check_out()
            except Exception:
                _logger.exception(
                    "Automatic check-out did not take place for reservation %s",
                    rec.name
                )

    @api.onchange('room_id')
    def set_room_price(self):
        self.room_price=self.room_id.room_price


    @api.model
    def _blocking_domain(self, room_ids, check_in, check_out):
        """ერთადერტი ადგილი, სადაც განისაზღვრება რომელი ჯავშანი აკავებს ოთახს:
        confirmed, checked_in და ვადაგაუსვლელი pending."""
        now = fields.Datetime.now()
        domain = [
            ('check_in', '<', check_out),
            ('check_out', '>', check_in),
            '|',
            ('state', 'in', ('confirmed', 'checked_in')),
            '&', ('state', '=', 'pending'), ('hold_expires_at', '>', now),
        ]
        if room_ids is not None:
            domain.insert(0, ('room_id', 'in', room_ids))
        return domain

    def _get_conflicts(self):
        self.ensure_one()
        domain = self._blocking_domain([self.room_id.id], self.check_in, self.check_out)
        return self.sudo().search(domain + [('id', '!=', self.id)])

    def action_sent_pending(self):
        hours = int(self.env['ir.config_parameter'].sudo().get_param('hotel_erp.pending_hold_hours', 24))
        now = fields.Datetime.now()
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError('Moving to "pending" is possible only for draft bookings.')
            # შემოწმება write-მდე, რომ შეცდომისას ბაზაში ნახევრად შეცვლილი ჩანაწერი არ დარჩეს
            if rec._get_conflicts():
                raise ValidationError(
                    f"The room '{rec.room_id.room_number}' is already occupied for the selected dates.!"
                )
            rec.write({
                'state': 'pending',
                'pending_date': now,
                'hold_expires_at': now + timedelta(hours=hours),
            })

    @api.model
    def _cron_expire_pending(self):
        expired = self.search([
            ('state', '=', 'pending'),
            ('hold_expires_at', '<', fields.Datetime.now()),
        ])
        expired.write({'state': 'expired'})


    def write(self, vals):
        
        for rec in self:
            if rec.state == 'checked_out':
                raise ValidationError('Checked Out It is forbidden to change the reservation data in the status!')
        res = super().write(vals)

        if 'room_id' in vals and 'room_price' not in vals:
            for rec in self.filtered(lambda r: r.state in ('draft', 'pending')):
                rec.room_price = rec.room_id.room_price

        if 'check_out' in vals:
            for rec in self:
                if rec.invoice_id and rec.invoice_id.state == 'posted':
                    dgeebi = max((rec.check_out - rec.check_in).days, 1)
                    invoice = rec.invoice_id.sudo()
                    invoice.button_draft()
                    for line in invoice.invoice_line_ids:
                        line.sudo().write({'quantity': dgeebi})
                    invoice.action_post()


    @api.depends('invoice_id', 'invoice_id.payment_state', 'service_invoice_ids', 'service_invoice_ids.payment_state',
                 'advance_payment_ids.state')
    def _compute_payment_ids(self):
        for rec in self:
            payments = rec.env['account.payment'].sudo()
            if rec.invoice_id:
                payments |= rec.invoice_id.sudo()._get_reconciled_payments()
            for inv in rec.service_invoice_ids.sudo():
                payments |= inv.sudo()._get_reconciled_payments()
            direct_advances = rec.advance_payment_ids.filtered(lambda p: p.state in ('paid', 'in_process'))
            payments |= direct_advances
            rec.payment_ids = [(6, 0, payments.ids)]

    @api.depends('total_price', 'paid_amount')
    def _compute_amount_due(self):
        for rec in self:
            if rec.total_price > rec.paid_amount:
                rec.amount_due = rec.total_price - rec.paid_amount
            else:
                rec.amount_due = 0.0

    @api.depends('paid_amount', 'total_price','state')
    def _compute_change_to_return(self):
        for rec in self:
            if rec.state=='cancelled':
                rec.change_to_return = rec.paid_amount
            elif rec.paid_amount > rec.total_price:
                rec.change_to_return = rec.paid_amount - rec.total_price
            else:
                rec.change_to_return = 0.0


    #თანხის დაბრუნების ლოგიკა
    def action_refund(self):
        self.ensure_one()
        if self.change_to_return <=0:
            raise ValidationError("No refundable amount is charged")
        if not self.guest_id.partner_id:
            raise ValidationError('The guest does not have an associated partner (res.partner).')

        return{
            'name':'Refund',
            'type':'ir.actions.act_window',
            'res_model':'account.payment',
            'view_mode':'form',
            'target':'new',
            'context':{
                'default_payment_type':'outbound',
                'default_partner_type':'customer',
                'default_partner_id':self.guest_id.partner_id.id,
                'default_amount':self.change_to_return,
                'default_reservation_id':self.id,
            }
        }

    @api.depends('invoice_id.amount_total', 'invoice_id.amount_residual',
                 'service_invoice_ids.amount_total', 'service_invoice_ids.amount_residual',
                 'advance_payment_ids.state', 'advance_payment_ids.amount', 'advance_payment_ids.payment_type')
    def _compute_paid_amount_calculation(self):
        for rec in self:
            paid = 0.0
            reconciled_payments = rec.env['account.payment'].sudo()
            if rec.invoice_id:
                invoice = rec.invoice_id.sudo()
                paid += (invoice.amount_total - invoice.amount_residual)
                reconciled_payments |= invoice._get_reconciled_payments()
            for inv in rec.service_invoice_ids.sudo():
                paid += (inv.amount_total - inv.amount_residual)
                reconciled_payments |= inv._get_reconciled_payments()

            unreconciled_advances = rec.advance_payment_ids.filtered(
                lambda p: p.state in ('paid', 'in_process') and p.id not in reconciled_payments.ids
            )
            inbound_sum = sum(unreconciled_advances.filtered(lambda p: p.payment_type == 'inbound').mapped('amount'))
            outbound_sum = sum(unreconciled_advances.filtered(lambda p: p.payment_type == 'outbound').mapped('amount'))
            paid += (inbound_sum - outbound_sum)

            rec.paid_amount = paid

    @api.depends('paid_amount', 'total_price', 'invoice_id.payment_state', 'service_invoice_ids.payment_state')
    def _compute_payment_status(self):
        for rec in self:
            if rec.paid_amount > rec.total_price and rec.total_price > 0:
                rec.payment_status = 'overpaid'
            elif rec.total_price > 0 and rec.paid_amount >= rec.total_price:
                rec.payment_status = 'paid'
            elif rec.paid_amount > 0:
                rec.payment_status = 'partial'
            else:
                rec.payment_status = 'unpaid'

    @api.depends('room_id', 'check_in', 'check_out', 'service_line_ids.price_subtotal','room_price')
    def _compute_total_price(self):
        for rec in self:
            if rec.room_id and rec.check_in and rec.check_out:
                dgeebi = max((rec.check_out - rec.check_in).days, 1)
                rec.total_price = (dgeebi * rec.room_price) + sum(rec.service_line_ids.mapped('price_subtotal'))
            else:
                rec.total_price = 0.0

    @api.constrains('check_in', 'check_out')
    def _check_dates(self):
        today = fields.Date.today()
        for rec in self:
            if rec.check_in and rec.check_out:
                if rec.check_out <= rec.check_in:
                    raise ValidationError("The check-out date must be the day after the check-in date.")
            if rec.check_in and rec.check_in < today:
                raise ValidationError(f"The check-in date cannot be earlier than today's date. Today is {today}.")
            if rec.check_out and rec.check_out < today:
                raise ValidationError(f"The check-out date cannot be earlier than today's date. Today is {today}.")

    @api.constrains('guest_id')
    def _check_guest_id_active(self):
        for rec in self:
            if rec.guest_id and not rec.guest_id.active:
                raise ValidationError('Archived users cannot create reservations.')

    @api.constrains('room_id', 'check_in', 'check_out', 'state')
    def _check_room_available(self):
        for rec in self:
            if not rec.room_id or not rec.check_in or not rec.check_out:
                continue
            if rec.state not in ('pending', 'confirmed', 'checked_in') or not rec.active:
                continue
            if rec.check_out <= rec.check_in:
                raise ValidationError('The check-out date must be later than the check-in date!')
            if rec._get_conflicts():
                raise ValidationError(
                    f"Room '{rec.room_id.room_number}' is already booked for the selected dates!"
                )

    @api.onchange('room_id', 'check_in', 'check_out')
    def _onchange_check_dates(self):
        if self.room_id and self.check_in and self.check_out and self.check_out > self.check_in:
            domain = self._blocking_domain([self.room_id.id], self.check_in, self.check_out)
            if self._origin:
                domain.append(('id', '!=', self._origin.id))
            if self.sudo().search_count(domain):
                return {
                    'warning': {
                        'title': '⚠️ The room is occupied.!',
                        'message': f'Room "{self.room_id.room_number}" is already booked for the selected interval.',
                    }
                }

    def unlink(self):
        return super().unlink()

    def action_confirm(self):
        now=fields.Datetime.now()
        for rec in self:
            if rec.state not in ('draft', 'pending'):
                raise ValidationError('Confirmation is possible only for Draft or Pending bookings.')
            if rec.paid_amount <= 0:
                raise ValidationError("Prepayment is required to confirm the reservation (use the 'Prepayment' button.)")
            if rec._get_conflicts():
                raise ValidationError(
                    f"Room '{rec.room_id.room_number}' is already booked for the selected dates!"
                )
            rec.write({'state': 'confirmed', 'hold_expires_at': False,'confirmed_at': now,'confirmed_by':self.env.user.id})

    def action_check_in(self):
        now=fields.Datetime.now()
        for rec in self:
            if rec.state != 'confirmed':
                raise ValidationError('Check-in is not possible for an unconfirmed reservation.')
            if rec.room_id.is_occupied_now:
                raise ValidationError('The room is occupied on this date; check-in is not possible!')
            if rec.room_id.housekeeping_status != 'clean':
                raise ValidationError('Check-in is not possible in an uncleaned room!')
            rec.write({'state':'checked_in','checked_in_at': now})
            if rec.room_id:
                rec.room_id.write({'room_status':'occupied'})

            if not rec.invoice_id:
                rec.action_create_invoice()
            rec.guest_id.message_post(
                body=f"Guest <b>{rec.guest_id.name}</b> has checked in to room <b>{rec.room_id.room_number}</b>."
            )

    def action_check_out(self):
        now = fields.Datetime.now()
        for rec in self:
            today = fields.Date.today()

            # 1. თარიღის შემოწმება
            if today < rec.check_out:
                raise ValidationError(
                    f"Today is {today} and the scheduled Check-Out date is {rec.check_out}. " 
f"If you want to leave early, change the Check-Out date."
                )

            # 2. გადახდის შემოწმება (სანამ სტატუსს შევცვლით ან მეილს გავაგზავნით!)
            if rec.total_price > 0 and rec.paid_amount < rec.total_price:
                raise ValidationError(
                    "The booking amount has not been fully paid; please settle the balance before checking out.")

            # 3. სტატუსის განახლება ბაზაში
            rec.sudo().write({'state': 'checked_out','checked_out_at': now})

            # 4. ინვოისების გაგზავნა მეილზე
            if rec.invoice_id:
                rec._send_invoice_by_email(rec.invoice_id)

            for invoice in rec.service_invoice_ids:
                rec._send_invoice_by_email(invoice)

            # 5. ჩანაწერი ლოგში და ოთახის სტატუსის შეცვლა
            rec.guest_id.message_post(
                body=f"Guest has checked out of the hotel. Reservation: <b>{rec.name}</b>, room: <b>{rec.room_id.room_number}</b>."
            )
            rec.room_id.sudo().write({'housekeeping_status': 'dirty', 'room_status': 'available'})

    def action_cancel(self,reason=None):
        now=fields.Datetime.now()
        reason=(reason or '').strip()[:500]
        for rec in self:
            if rec.state not in ('draft', 'pending', 'confirmed'):
                raise ValidationError('call to cancel is not allowed')
            vals={'state':'cancelled','hold_expires_at':False,'cancelled_at':now}
            if reason:
                vals['cancellation_reason'] = reason
            rec.write(vals)
            body=f"The booking <b>{rec.name}</b> has been successfully cancelled."
            if reason:
                body +=f"<br/>მიზეზი:{escape(reason)}"
            if rec.paid_amount>0:
                body+=f"<br/><b>⚠️ Paid {rec.paid_amount:.2f} {rec.currency_id.name} — Refund review required."
            rec.guest_id.sudo().message_post(body=body)


    #ვიზარდის გახსნის მეთოდი
    def action_open_cancel_wizard(self):
        self.ensure_one()
        return {
            'name': 'Booking Cancellation',
            'type': 'ir.actions.act_window',
            'res_model': 'hotel.reservation.cancel.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context':{'default_reservation_id':self.id}
        }
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('hotel.reservation')

            if not vals.get('room_price') and vals.get('room_id'):
                vals['room_price'] = self.env['hotel.room'].browse(vals['room_id']).room_price
        return super().create(vals_list)

    def action_view_invoice(self):
        self.ensure_one()
        return {
            'name': 'Invoice',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'view_mode': 'form',
            'target': 'current'
        }

    def action_view_service_invoices(self):
        self.ensure_one()
        return {
            'name': 'Service Invoices',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.service_invoice_ids.ids)],
        }

    def action_register_advance_payment(self):
        self.ensure_one()
        if not self.guest_id.partner_id:
            raise ValidationError('The guest does not have an associated partner (res.partner); the prepayment cannot be processed.')

        if self.amount_due <= 0:
            raise ValidationError('There is no credit on the booking, no payment can be made.')

        view_id=self.env.ref('hotel_erp.hotel_erp_payment_form_view').id
        return {
            'name': 'Prepayment / Deposit',
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'target': 'new',
            'context': {
                'default_payment_type': 'inbound',
                'default_partner_type': 'customer',
                'default_partner_id': self.guest_id.partner_id.id,
                'default_amount': self.amount_due,
                'default_reservation_id': self.id,
            }
        }

    def _send_invoice_by_email(self, invoice):
        self.ensure_one()
        partner = self.guest_id.partner_id
        if not partner.email:
            raise ValidationError("The guest does not have an email address.")
        email_from = self.env.company.email or self.env.user.email

        pdf_content, content_type = self.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'account.account_invoices', [invoice.id]
        )
        attachment = self.env['ir.attachment'].sudo().create({
            'name': f'{invoice.name}.pdf',
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': 'account.move',
            'res_id': invoice.id,
            'mimetype': 'application/pdf',
        })
        mail = self.env['mail.mail'].sudo().create({
            'subject': f'Invoice {invoice.name} - {self.name}',
            'body_html': f"""
                <p>Hello {partner.name},</p>
                <p>I am sending you the invoice <strong>{invoice.name}</strong> for your hotel booking.</p>
                <p>Reservation: <strong>{self.name}</strong></p>
                <p>Invoice amount: <strong>{invoice.amount_total:.2f} {self.currency_id.name or 'GEL'}</strong></p>
                <p>Thank you for using our hotel's services.</p>
            """,
            'email_from': email_from,
            'email_to': partner.email,
            'attachment_ids': [(4, attachment.id)]
        })
        mail.sudo().send()
        return True

    def _send_payment_confirmation_email(self, payment_amount):
        self.ensure_one()
        partner = self.guest_id.partner_id
        if not partner or not partner.email:
            return False

        room_total = 0.0
        if self.room_id and self.check_in and self.check_out:
            days = max((self.check_out - self.check_in).days, 1)
            room_total = days * self.room_price

        service_total = sum(line.price_subtotal for line in self.service_line_ids)
        grand_total = self.total_price
        total_paid = self.paid_amount
        amount_due = max(grand_total - total_paid, 0.0)

        if total_paid <= 0:
            payment_status = "Unpaid"
        elif total_paid < grand_total:
            payment_status = "Partially Paid"
        elif total_paid == grand_total:
            payment_status = "Paid"
        else:
            payment_status = "Overpaid"

        email_from = self.env.company.email or self.env.user.email
        currency = self.currency_id.name or "GEL"

        body_html = f"""
            <div style="font-family: Arial, sans-serif;">
                <h2>Payment Confirmation</h2>
                <p>Hello <strong>{partner.name}</strong>,</p>
                <p>We confirm the payment made for your hotel reservation.</p>
                <hr/>
                <h3>Reservation Information</h3>
                <p>
                    <strong>Reservation:</strong> {self.name}<br/>
                    <strong>Room:</strong> {self.room_id.room_number if self.room_id else '-'}<br/>
                    <strong>Check-in:</strong> {self.check_in or '-'}<br/>
                    <strong>Check-out:</strong> {self.check_out or '-'}
                </p>
                <hr/>
                <h3>Payment Summary</h3>
                <table style="border-collapse: collapse; width: 100%; max-width: 600px;">
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;">Room cost</td>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;"><strong>{room_total:.2f} {currency}</strong></td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;">Services Cost</td>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;"><strong>{service_total:.2f} {currency}</strong></td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border-bottom: 2px solid #333;"><strong>Total Value</strong></td>
                        <td style="padding: 8px; border-bottom: 2px solid #333; text-align: right;"><strong>{grand_total:.2f} {currency}</strong></td>
                    </tr>
                    <tr>
                        <td style="padding: 8px;">Current payment</td>
                        <td style="padding: 8px; text-align: right;"><strong>{payment_amount:.2f} {currency}</strong></td>
                    </tr>
                    <tr>
                        <td style="padding: 8px;">Total paid</td>
                        <td style="padding: 8px; text-align: right;"><strong>{total_paid:.2f} {currency}</strong></td>
                    </tr>
                    <tr>
                        <td style="padding: 8px;">Remaining amount</td>
                        <td style="padding: 8px; text-align: right;"><strong>{amount_due:.2f} {currency}</strong></td>
                    </tr>
                    <tr>
                        <td style="padding: 8px;">Payment Status</td>
                        <td style="padding: 8px; text-align: right;"><strong>{payment_status}</strong></td>
                    </tr>
                </table>
                <br/>
                <p>Thank you for using our hotel's services.</p>
                <p>Respectfully,<br/><strong>{self.env.company.name}</strong></p>
            </div>
        """

        mail = self.env['mail.mail'].sudo().create({
            'subject': f'Payment Confirmation - {self.name}',
            'body_html': body_html,
            'email_from': email_from,
            'email_to': partner.email,
        })
        mail.sudo().send()
        return True

    def action_create_invoice(self):
        for rec in self:
            if rec.state not in ('checked_in', 'checked_out'):
                raise ValidationError('Room invoice can be created only after Check-in')
            if rec.invoice_id:
                raise ValidationError('A room invoice has already been issued for this reservation')
            if not rec.guest_id.partner_id:
                raise ValidationError('An invoice cannot be issued without `res.partner`.')

            invoice_lines = []
            if rec.room_id and rec.check_in and rec.check_out:
                day = max((rec.check_out - rec.check_in).days, 1)
                invoice_lines.append((0, 0, {
                    'name': f"Renting a room:{rec.room_id.room_number}",
                    'quantity': day,
                    'price_unit': rec.room_price
                }))

            invoice = self.env['account.move'].sudo().create({
                'move_type': 'out_invoice',
                'partner_id': rec.guest_id.partner_id.id,
                'invoice_date': fields.Date.context_today(rec),
                'invoice_line_ids': invoice_lines
            })

            invoice.sudo().action_post()
            rec.invoice_id = invoice.id

            # Odoo 18: Reconcile-ისთვის გამოიყენება payment.move_id.line_ids და სტატუსები ('paid', 'in_process')
            for payment in rec.advance_payment_ids.filtered(lambda p: p.state in ('paid', 'in_process')):
                payment_lines = payment.move_id.line_ids if payment.move_id else rec.env['account.move.line']
                lines = (payment_lines + invoice.line_ids).filtered(
                    lambda l: l.account_id == rec.guest_id.partner_id.property_account_receivable_id and not l.reconciled
                )
                if len(lines) >= 2:
                    lines.reconcile()

            rec.guest_id.message_post(
                body=f"A room invoice has been created for the reservation <b>{rec.name}</b>: <b>{invoice.name}</b> (Total: {invoice.amount_total} GEL)",
                subject='Create an invoice',
                message_type='notification',
                subtype_xmlid='mail.mt_note'
            )
        return True

    def action_create_service_invoice(self):
        for rec in self:
            uninvoiced_lines = rec.service_line_ids.filtered(lambda l: not l.invoiced)
            if not uninvoiced_lines:
                continue
            if not rec.guest_id.partner_id:
                raise ValidationError('An invoice cannot be issued without `res.partner`.')

            invoice_lines = [(0, 0, {
                'name': line.service_id.name,
                'quantity': line.quantity,
                'price_unit': line.price_unit,
            }) for line in uninvoiced_lines]

            invoice = self.env['account.move'].sudo().create({
                'move_type': 'out_invoice',
                'partner_id': rec.guest_id.partner_id.id,
                'invoice_date': fields.Date.context_today(rec),
                'invoice_line_ids': invoice_lines,
            })
            invoice.sudo().action_post()

            rec.service_invoice_ids = [(4, invoice.id)]
            uninvoiced_lines.write({'invoiced': True})

            # 🔗 წინასწარი გადახდის (Advance Payment) ავტომატური მიბმა სერვისის ინვოისზე
            for payment in rec.advance_payment_ids.filtered(lambda p: p.state in ('paid', 'in_process', 'posted')):
                payment_lines = payment.move_id.line_ids if payment.move_id else rec.env['account.move.line']
                lines = (payment_lines + invoice.line_ids).filtered(
                    lambda
                        l: l.account_id == rec.guest_id.partner_id.property_account_receivable_id and not l.reconciled
                )
                if len(lines) >= 2:
                    lines.reconcile()

            rec.guest_id.message_post(
                body=f"An invoice for additional services has been created for the booking <b>{rec.name}</b>: "
                     f"<b>{invoice.name}</b> (Sum: {invoice.amount_total} GEL)",
                subject='Service Invoice',
                message_type='notification',
                subtype_xmlid='mail.mt_note'
            )
        return True


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    reservation_id = fields.Many2one('hotel.reservation', string="Reservation")

    def action_post(self):
        res = super().action_post()
        for payment in self:
            if payment.reservation_id:
                # გადახდის ან თანხის დაბრუნების შემდეგ იძულებით ვახდენთ ველების გადათვლას
                payment.reservation_id._compute_paid_amount_calculation()
                payment.reservation_id._compute_amount_due()
                payment.reservation_id._compute_payment_status()
                payment.reservation_id._compute_change_to_return()

                if payment.state == 'in_process':
                    payment.state = 'paid'

                # მხოლოდ შემოსულ გადახდებზე (inbound) ადასტურებს ჯავშანს და აგზავნის მეილს
                if payment.payment_type == 'inbound':
                    if payment.reservation_id.state in ('draft', 'pending'):
                        payment.reservation_id.action_confirm()
                    payment.reservation_id._send_payment_confirmation_email(payment.amount)
        return res