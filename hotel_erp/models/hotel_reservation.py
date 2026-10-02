import base64
from datetime import timedelta
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HotelReservation(models.Model):
    _name = 'hotel.reservation'
    _description = 'Hotel Reservation'

    name = fields.Char(string="Reservation Reference", default='New', required=True)
    guest_id = fields.Many2one('hotel.guest', string='Guest', required=True)
    room_id = fields.Many2one('hotel.room', string='Room', required=True)
    check_in = fields.Date(string="Check In", required=True)
    check_out = fields.Date(string="Check Out", required=True)
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        default=lambda self: self.env.company.currency_id, readonly=True
    )
    room_price = fields.Monetary( currency_field='currency_id',string='ოთახის ფასი(1 ღამე)', readonly=True, store=True)
    pending_date=fields.Datetime(string="Pending Date", readonly=True)
    hold_expires_at = fields.Datetime(string="Hold Expires At", readonly=True, copy=False)
    confirmed_at = fields.Datetime(string="Confirmed At", readonly=True, copy=False)
    confirmed_by = fields.Many2one('res.users', string="Confirmed By", readonly=True, copy=False)
    cancelled_at = fields.Datetime(string="Cancelled At", readonly=True, copy=False)
    cancellation_reason = fields.Text(string="Cancellation Reason", copy=False)
    checked_in_at = fields.Datetime(string="Checked In At", readonly=True, copy=False)
    checked_out_at = fields.Datetime(string="Checked Out At", readonly=True, copy=False)
    total_price = fields.Monetary(
        string="Total Price", currency_field='currency_id',
        compute="_compute_total_price", store=True
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('checked_in', 'Checked In'),
        ('checked_out', 'Checked Out'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('no_show', 'No Show'),
    ], string='State', default="draft")

    service_line_ids = fields.One2many('hotel.reservation.line', 'reservation_id', string="Service Lines")
    invoice_id = fields.Many2one(
        'account.move', string="Room Invoice", readonly=True, copy=False,
        help="ოთახის ღირებულების ინვოისი."
    )
    service_invoice_ids = fields.Many2many(
        'account.move', 'hotel_reservation_service_invoice_rel',
        'reservation_id', 'invoice_id', string="Service Invoices", readonly=True, copy=False,
        help="დამატებითი სერვისების ინვოისები."
    )

    advance_payment_ids = fields.One2many(
        'account.payment', 'reservation_id',
        string="წინასწარი გადახდები / დეპოზიტები", readonly=True
    )

    payment_ids = fields.Many2many('account.payment', string="Payments", compute="_compute_payment_ids", readonly=True)
    paid_amount = fields.Monetary(
        string="Paid Amount", currency_field='currency_id',
        compute="_compute_paid_amount_calculation", store=True
    )
    residual_amount = fields.Monetary(
        string="Residual Amount", currency_field='currency_id',
        compute="_compute_residual_amount_calculation", store=True
    )
    payment_status = fields.Selection(
        [('unpaid', 'Unpaid'), ('partial', 'Partially Paid'), ('paid', 'Paid'), ('overpaid', 'Overpaid')],
        compute="_compute_payment_status", store=True
    )
    amount_due = fields.Monetary(
        string="დარჩენილი დავალიანება", currency_field='currency_id',
        compute="_compute_amount_due", store=True
    )
    change_to_return = fields.Monetary(
        string="დასაბრუნებელი ხურდა", currency_field='currency_id',
        compute='_compute_change_to_return'
    )
    active = fields.Boolean(string="Active", default=True)



    @api.onchange(room_id)
    def set_room_price(self):
        self.room_price=self.room_id.price

    def action_no_show(self):
        for rec in self:
            if rec.state !='confirmed':
                raise ValidationError('დაუდასტურებელი ჯავშნიდან ვერ განახორციელებთ ამ ქმედებას(action_no_show)')
            if rec.check_in >= fields.Date.today():
                raise ValidationError('შემოსვლის თარიღი აღემატება დღევანდელ დღეს და ვერ განახორციელებთ ქმედებას:(action_no_show)')
            rec.state='no_show'
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
                raise ValidationError('pending-ზე გადაყვანა შესაძლებელია მხოლოდ draft ჯავშნებისათვის')
            # შემოწმება write-მდე, რომ შეცდომისას ბაზაში ნახევრად შეცვლილი ჩანაწერი არ დარჩეს
            if rec._get_conflicts():
                raise ValidationError(
                    f"ოთახი '{rec.room_id.room_number}' არჩეულ თარიღებში უკვე დაკავებულია!"
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
                raise ValidationError('Checked Out სტატუსში მყოფი ჯავშნის მონაცემების შეცვლა აკრძალულია!')

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

        return res

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

    @api.depends('paid_amount', 'total_price')
    def _compute_change_to_return(self):
        for rec in self:
            if rec.paid_amount > rec.total_price:
                rec.change_to_return = rec.paid_amount - rec.total_price
            else:
                rec.change_to_return = 0.0

    @api.depends('invoice_id.amount_total', 'invoice_id.amount_residual',
                 'service_invoice_ids.amount_total', 'service_invoice_ids.amount_residual',
                 'advance_payment_ids.state', 'advance_payment_ids.amount')
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
            paid += sum(unreconciled_advances.mapped('amount'))
            rec.paid_amount = paid

    @api.depends('total_price', 'paid_amount')
    def _compute_residual_amount_calculation(self):
        for rec in self:
            rec.residual_amount = max(rec.total_price - rec.paid_amount, 0.0)

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

    @api.depends('room_id', 'check_in', 'check_out', 'service_line_ids.price_subtotal')
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
                    raise ValidationError("Check-out-ის თარიღი უნდა იყოს check_in თარიღის მომდევნო")
            if rec.check_in and rec.check_in < today:
                raise ValidationError(f"Check-In-ის თარიღი არ შეიძლება იყოს დღევანდელ თარიღზე ადრე. დღეს არის {today}.")
            if rec.check_out and rec.check_out < today:
                raise ValidationError(f"Check-Out-ის თარიღი არ შეიძლება იყოს დღევანდელ თარიღზე ადრე. დღეს არის {today}.")

    @api.constrains('guest_id')
    def _check_guest_id_active(self):
        for rec in self:
            if rec.guest_id and not rec.guest_id.active:
                raise ValidationError('დაარქივებულ მომხმარებელს არ შეუძლია ჯავშნის შექმნა')

    @api.constrains('room_id', 'check_in', 'check_out', 'state')
    def _check_room_available(self):
        for rec in self:
            if not rec.room_id or not rec.check_in or not rec.check_out:
                continue
            if rec.state not in ('pending', 'confirmed', 'checked_in') or not rec.active:
                continue
            if rec.check_out <= rec.check_in:
                raise ValidationError('Check-out თარიღი უნდა იყოს Check-in-ზე გვიან!')
            if rec._get_conflicts():
                raise ValidationError(
                    f"ოთახი '{rec.room_id.room_number}' არჩეულ თარიღებში უკვე დაკავებულია!"
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
                        'title': '⚠️ ოთახი დაკავებულია!',
                        'message': f'ოთახი "{self.room_id.room_number}" არჩეულ ინტერვალში უკვე დაჯავშნილია.',
                    }
                }

    def unlink(self):
        return super().unlink()

    def action_confirm(self):
        now=fields.Datetime.now()
        for rec in self:
            if rec.state not in ('draft', 'pending'):
                raise ValidationError('დადასტურება შესაძლებელია მხოლოდ Draft ან Pending ჯავშნისთვის')
            if rec.paid_amount <= 0:
                raise ValidationError("ჯავშნის დასადასტურებლად აუცილებელია წინასწარი გადახდის განხორციელება,(გამოიყენეთ 'წინასწარი გადახდის' ღილაკი.)")
            if rec._get_conflicts():
                raise ValidationError(
                    f"ოთახი '{rec.room_id.room_number}' არჩეულ თარიღებში უკვე დაკავებულია!"
                )
            rec.write({'state': 'confirmed', 'hold_expires_at': False,'confirmed_at': now,'confirmed_by':self.env.user.id})

    def action_check_in(self):
        now=fields.Datetime.now()
        for rec in self:
            if rec.state != 'confirmed':
                raise ValidationError('დაუდასტურებელი ჯავშანის Check_in არ შეიძლება')
            if rec.room_id.room_status != 'available':
                raise ValidationError('ოთახი რემონტშია ან არააქტიურია, Check-in შეუძლებელია!')
            if rec.room_id.housekeeping_status != 'clean':
                raise ValidationError('დაუსუფთავებელ ოთახში Check-in შეუძლებელია!')
            rec.write({'state':'checked_in','checked_in_at': now})
            if rec.room_id:
                rec.room_id.write({'room_status':'occupied'})

            if not rec.invoice_id:
                rec.action_create_invoice()
            rec.guest_id.message_post(
                body=f"სტუმარი <b>{rec.guest_id.name}</b> დარეგისტრირდა (Check-In) ოთახში <b>{rec.room_id.room_number}</b>."
            )

    def action_check_out(self):
        now=fields.Datetime.now()
        for rec in self:
            today = fields.Date.today()
            if today < rec.check_out:
                raise ValidationError(
                    f"დღეს არის {today}, ხოლო დაგეგმილი Check-Out-ის თარიღია {rec.check_out}. "
                    f"თუ გსურთ დროზე ადრე გასვლა, შეცვალეთ Check-Out-ის თარიღი."
                )
            rec.sudo().write({'state': 'checked_out', 'active': False,'checked_out_at':now})
            if rec.invoice_id:
                rec._send_invoice_by_email(rec.invoice_id)
            for invoice in rec.service_invoice_ids:
                rec._send_invoice_by_email(invoice)

            rec.guest_id.message_post(
                body=f"სტუმარმა დატოვა სასტუმრო. ჯავშანი: <b>{rec.name}</b>, ოთახი: <b>{rec.room_id.room_number}</b>."
            )
            rec.room_id.sudo().write({'housekeeping_status': 'dirty','room_id.room_status':'available'})

    def action_cancel(self):
        now=fields.Datetime.now()
        for rec in self:
            if rec.state not in ('draft', 'pending', 'confirmed'):
                raise ValidationError('cancel ის გამოძახება დაუშვებელია')
            rec.write({'state': 'cancelled', 'hold_expires_at': False,'cancelled_at': now})

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
            raise ValidationError('სტუმარს არ აქვს მიბმული პარტნიორი (res.partner), წინასწარი გადახდა ვერ გატარდება.')

        if self.amount_due <= 0:
            raise ValidationError('ჯავშანზე დავალიანება არ ირიცხება, გადახდა ვერ განხორციელდება.')
        return {
            'name': 'წინასწარი გადახდა / დეპოზიტი',
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'form',
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
            raise ValidationError("სტუმარს არ აქვს email მისამართი.")
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
                <p>გამარჯობა {partner.name},</p>
                <p>გიგზავნით თქვენი სასტუმროს ჯავშნის <strong>{invoice.name}</strong> ინვოისს.</p>
                <p>ჯავშანი: <strong>{self.name}</strong></p>
                <p>ინვოისის თანხა: <strong>{invoice.amount_total:.2f} {self.currency_id.name or 'GEL'}</strong></p>
                <p>მადლობა, რომ სარგებლობთ ჩვენი სასტუმროს მომსახურებით.</p>
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
                <p>გამარჯობა <strong>{partner.name}</strong>,</p>
                <p>გიდასტურებთ თქვენი სასტუმროს ჯავშანზე განხორციელებულ გადახდას.</p>
                <hr/>
                <h3>Reservation Information</h3>
                <p>
                    <strong>ჯავშანი:</strong> {self.name}<br/>
                    <strong>ოთახი:</strong> {self.room_id.room_number if self.room_id else '-'}<br/>
                    <strong>Check-in:</strong> {self.check_in or '-'}<br/>
                    <strong>Check-out:</strong> {self.check_out or '-'}
                </p>
                <hr/>
                <h3>Payment Summary</h3>
                <table style="border-collapse: collapse; width: 100%; max-width: 600px;">
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;">ოთახის ღირებულება</td>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;"><strong>{room_total:.2f} {currency}</strong></td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;">სერვისების ღირებულება</td>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;"><strong>{service_total:.2f} {currency}</strong></td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border-bottom: 2px solid #333;"><strong>ჯამური ღირებულება</strong></td>
                        <td style="padding: 8px; border-bottom: 2px solid #333; text-align: right;"><strong>{grand_total:.2f} {currency}</strong></td>
                    </tr>
                    <tr>
                        <td style="padding: 8px;">მიმდინარე გადახდა</td>
                        <td style="padding: 8px; text-align: right;"><strong>{payment_amount:.2f} {currency}</strong></td>
                    </tr>
                    <tr>
                        <td style="padding: 8px;">სულ გადახდილი</td>
                        <td style="padding: 8px; text-align: right;"><strong>{total_paid:.2f} {currency}</strong></td>
                    </tr>
                    <tr>
                        <td style="padding: 8px;">დარჩენილი თანხა</td>
                        <td style="padding: 8px; text-align: right;"><strong>{amount_due:.2f} {currency}</strong></td>
                    </tr>
                    <tr>
                        <td style="padding: 8px;">Payment Status</td>
                        <td style="padding: 8px; text-align: right;"><strong>{payment_status}</strong></td>
                    </tr>
                </table>
                <br/>
                <p>მადლობა, რომ სარგებლობთ ჩვენი სასტუმროს მომსახურებით.</p>
                <p>პატივისცემით,<br/><strong>{self.env.company.name}</strong></p>
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
                raise ValidationError('ოთახის ინვოისის შექმნა შესაძლებელია მხოლოდ Check-in-ის შემდეგ')
            if rec.invoice_id:
                raise ValidationError('ამ ჯავშანზე ოთახის ინვოისი უკვე გაცემულია')
            if not rec.guest_id.partner_id:
                raise ValidationError('res.partner-ის გარეშე ინვოისი არ გაიცემა')

            invoice_lines = []
            if rec.room_id and rec.check_in and rec.check_out:
                day = max((rec.check_out - rec.check_in).days, 1)
                invoice_lines.append((0, 0, {
                    'name': f"ოთახის ქირაობა:{rec.room_id.room_number}",
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
                body=f"ჯავშანზე <b>{rec.name}</b> შეექმნა ოთახის ინვოისი: <b>{invoice.name}</b> (ჯამი: {invoice.amount_total} GEL)",
                subject='ინვოისის შექმნა',
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
                raise ValidationError('res.partner-ის გარეშე ინვოისი არ გაიცემა')

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
                body=f"ჯავშანზე <b>{rec.name}</b> დამატებით სერვისებზე შეიქმნა ინვოისი: "
                     f"<b>{invoice.name}</b> (ჯამი: {invoice.amount_total} GEL)",
                subject='სერვისის ინვოისი',
                message_type='notification',
                subtype_xmlid='mail.mt_note'
            )
        return True


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    reservation_id = fields.Many2one('hotel.reservation', string="ჯავშანი")

    def action_post(self):
        res = super().action_post()
        for payment in self:
            if payment.reservation_id:
                # გადახდის შემდეგ იძულებით ვახდენთ გამოთვლითი ველების განახლებას
                payment.reservation_id._compute_paid_amount_calculation()
                payment.reservation_id._compute_amount_due()
                payment.reservation_id._compute_payment_status()

                if payment.reservation_id and payment.state=='in_process':
                    payment.state='paid'

                if payment.reservation_id.state in ('draft', 'pending'):
                    payment.reservation_id.action_confirm()
                payment.reservation_id._send_payment_confirmation_email(payment.amount)
        return res