from odoo import models,fields,api
from odoo.exceptions import ValidationError

class HotelReservation(models.Model):
    _name='hotel.reservation'
    _description='Hotel Reservation'

    name=fields.Char(string="Reservation Reference",default='New',required=True)
    guest_id=fields.Many2one('hotel.guest',string='Guest',required=True)
    room_id=fields.Many2one('hotel.room',string='Room',required=True)
    check_in=fields.Date(string="Check In",required=True)
    check_out=fields.Date(string="Check Out", required=True)
    room_price=fields.Float(related='room_id.room_price',string='ოთახის ფასი(1 ღამე)',readonly=True,store=True)
    total_price=fields.Float(string="Total Price",compute="_compute_total_price",store=True)
    state=fields.Selection([('draft','Draft'),('confirmed','Confirmed'),('checked_in','Checked In'),('checked_out','Checked Out'),('cancelled','Cancelled')],string='State',default="draft")
    service_line_ids=fields.One2many('hotel.reservation.line','reservation_id',string="Service Lines")
    invoice_id=fields.Many2one('account.move',string="Room Invoice",readonly=True,copy=False,
                               help="ოთახის ღირებულების ინვოისი. იქმნება Check-in-ის მომენტში, რაც სტუმარს Check-out-მდე "
                                    "წინასწარ გადახდის საშუალებას აძლევს.")
    service_invoice_ids=fields.Many2many('account.move','hotel_reservation_service_invoice_rel',
                                         'reservation_id','invoice_id',string="Service Invoices",readonly=True,copy=False,
                                         help="დამატებითი სერვისების ინვოისები. შეიძლება რამდენიმეც შეიქმნას, თუ სტუმარმა სხვადასხვა დროს "
                                              "დაამატა სერვისი. ავტომატურად გენერირდება Check-out-ის დროს ნებისმიერი ჯერ არჩაინვოისებელი "
                                              "სერვის-ხაზისთვის.")
    payment_ids=fields.Many2many('account.payment',string="Payments",compute="_compute_payment_ids",readonly=True)
    paid_amount=fields.Float(string="Paid Amount",compute="_compute_paid_amount_calculation",store=True)
    residual_amount=fields.Float(string="Residual Amount",compute="_compute_residual_amount_calculation",store=True)
    payment_status=fields.Selection([('unpaid','Unpaid'),('partial','Partially Paid'),('paid','Paid'),('overpaid','Overpaid')],compute="_compute_payment_status",store=True)
    amount_due=fields.Float(string="დარჩენილი დავალიანება",compute="_compute_amount_due")
    change_to_return=fields.Float(string="დასაბრუნებელი ხურდა",compute='_compute_change_to_return')


    def write(self,vals):
        for rec in self:
            if rec.state=='checked_out':
                raise ValidationError('Checked Out სტატუსში მყოფი ჯავშნის მონაცემების შეცვლა აკრძალულია!')
        return super().write(vals)

    @api.depends('invoice_id','invoice_id.payment_state','service_invoice_ids','service_invoice_ids.payment_state')
    def _compute_payment_ids(self):
        for rec in self:
            payments = rec.env['account.payment'].sudo()
            if rec.invoice_id:
                payments |= rec.invoice_id.sudo()._get_reconciled_payments()
            for inv in rec.service_invoice_ids.sudo():
                payments |= inv.sudo()._get_reconciled_payments()
            rec.payment_ids=[(6,0,payments.ids)]
    @api.depends('total_price','paid_amount')
    def _compute_amount_due(self):
        for rec in self:
            if rec.total_price > rec.paid_amount:
                rec.amount_due=rec.total_price-rec.paid_amount
            else:
                rec.amount_due=0
    @api.depends('paid_amount','total_price')
    def _compute_change_to_return(self):
        for rec in self:
            if rec.paid_amount > rec.total_price:
                rec.change_to_return=rec.paid_amount - rec.total_price
            else:
                rec.change_to_return=0
    @api.depends('invoice_id.amount_total','invoice_id.amount_residual',
                 'service_invoice_ids.amount_total','service_invoice_ids.amount_residual')
    def _compute_paid_amount_calculation(self):
        for rec in self:
            paid = 0.0
            if rec.invoice_id:
                invoice=rec.invoice_id.sudo()
                paid += invoice.amount_total - invoice.amount_residual
            for inv in rec.service_invoice_ids.sudo():
                paid += inv.amount_total - inv.amount_residual
            rec.paid_amount = paid


    @api.depends('total_price','paid_amount')
    def _compute_residual_amount_calculation(self):
        for rec in self:
            rec.residual_amount=max(rec.total_price-rec.paid_amount,0.0)

    @api.depends('paid_amount','total_price','invoice_id.payment_state','service_invoice_ids.payment_state')
    def _compute_payment_status(self):
        for rec in self:

            if rec.paid_amount>rec.total_price:
                rec.payment_status='overpaid'

            elif  rec.total_price>0 and rec.paid_amount>=rec.total_price:
                rec.payment_status='paid'
            elif rec.paid_amount>0:
                rec.payment_status='partial'
            else:
                rec.payment_status='unpaid'

    @api.depends('room_id','check_in','check_out','service_line_ids.price_subtotal')
    def _compute_total_price(self):
        for rec in self:
            if rec.room_id and rec.check_in and rec.check_out:
                dgeebi=(rec.check_out - rec.check_in).days
                dgeebi=max(dgeebi,1)
                rec.total_price=(dgeebi * rec.room_id.room_price) + sum(rec.service_line_ids.mapped('price_subtotal'))
            else:
                rec.total_price=0.0

    @api.constrains('check_in','check_out')
    def _check_dates(self):
        for rec in self:
            if rec.check_in and rec.check_out:
                if rec.check_out <= rec.check_in:
                    raise ValidationError("Check-out-ის თარიღი უნდა იყოს check_in თარიღის მომთევნო")


    @api.constrains('guest_id')
    def _check_guest_id_active(self):
        for rec in self:
            if rec.guest_id:
                if rec.guest_id.active ==False:
                    raise ValidationError('დაარქივებულ მომხამრებელს არ შეუძლია ჯავშნის შექმნა')

    @api.constrains('room_id','check_in','check_out','state')
    def _check_room_available(self):
        for rec in self:
            if not rec.room_id or not rec.check_in or not rec.check_out:
                continue

            if rec.state == 'cancelled':
                continue

            if rec.check_out <= rec.check_in:
                raise ValidationError(
                    'Check-out თარიღი უნდა იყოს Check-in-ზე გვიან!'
                )

            # ვეძებთ იმავე ოთახზე გადაფარვად ჯავშნებს
            overlapping = self.search([
                ('id', '!=', rec.id),
                ('room_id', '=', rec.room_id.id),
                ('check_in', '<', rec.check_out),
                ('check_out', '>', rec.check_in),
                ('state', '!=', 'cancelled'),
            ])

            if overlapping:
                raise ValidationError(
                    f"ოთახი '{rec.room_id.room_number}' არჩეულ თარიღებში უკვე დაკავებულია!"
                )

        # ამოტანილია გარეთ, სწორ დონეზე:
        #pop-up ის გამოტანა მომხამრებლისათვის:

    @api.onchange('room_id', 'check_in', 'check_out')
    def _onchange_check_dates(self):
        if self.room_id and self.check_in and self.check_out:
            if self.check_out > self.check_in:
                overlapping = self.search([
                    ('id', '!=', self._origin.id if self._origin else False),
                    ('room_id', '=', self.room_id.id),
                    ('check_in', '<', self.check_out),
                    ('check_out', '>', self.check_in),
                    ('state', '!=', 'cancelled'),
                ])
                if overlapping:
                    return {
                        'warning': {
                            'title': '⚠️ ოთახი დაკავებულია!',
                            'message': (
                                f'ოთახი "{self.room_id.room_number}" არჩეულ ინტერვალში'
                                ' უკვე დაჯავშნილია. გთხოვთ აირჩიოთ სხვა'
                                ' თარიღი.'
                            ),
                        }
                    }
    def unlink(self):
        for record in self:
            if record.room_id:
                record.room_id.sudo().write({'room_status':'available'})
        res=super().unlink()
        return res

    def action_confirm(self):
        for rec in self:
            if rec.state == 'cancelled':
                raise ValidationError('გაუქმებული ჯავშნის დადასტურება შეუძლებელია')
            rec.state='confirmed'


    def action_check_in(self):
        for rec in self:
            if rec.room_id.housekeeping_status in ('dirty','maintenance'):
                raise ValidationError('დაუსუფთავებელ ან რემონტში მყოფ ოთახში Check-in შეუძლებელია!')
            if rec.state !='confirmed':
                raise ValidationError('დაუდასტურებელი ჯავშანის Check_in არ შეიძლება')
            rec.state='checked_in'
            rec.room_id.sudo().write({'room_status':'occupied'})
            # 🔑 Check-in-ის მომენტში ოთახის ინვოისი ავტომატურად იქმნება, რაც სტუმარს
            # Check-out-მდე წინასწარ გადახდის საშუალებას აძლევს.
            if not rec.invoice_id:
                rec.action_create_invoice()
            rec.guest_id.message_post(
                body=f"სტუმარი <b>{rec.guest_id.name}</b> დარეგისტრირდა (Check-In) ოთახში <b>{rec.room_id.room_number}</b>.")
    def action_check_out(self):
        for rec in self:
            if rec.state !='checked_in':
                raise ValidationError("Check_in-ის გარეშე Check_out-ზე გადაყვანა დაუშვებელია")
            today=fields.Date.today()
            if today < rec.check_out:
                raise ValidationError(f"Check-Out-ის გაკეთება შესაძლებელია მხოლოდ შეთანხმებულ თარიღში ({rec.check_out}). თუ სტუმარი ვადაზე ადრე გადის, ჯერ შეასწორეთ Check-Out თარიღი!")
            # 🔑 Check-out-ის წინ, ნებისმიერი დარჩენილი (ჯერ არჩაინვოისებელი) სერვის-ხაზი
            # ავტომატურად ინვოისდება — ასე აღარ დაგავიწყდება მოგვიანებით დამატებული სერვისის ჩარიცხვა.
            rec.action_create_service_invoice()
            if rec.amount_due>0:
                raise ValidationError('თქვენ აღგენიშნებათ დავალიანება და ვერ შეძლებთ check_out-ს სანამ ამ დავალიანებას არ გადაიხდით')
            if not rec.invoice_id:
                raise ValidationError('ინვოისი შექმნილი არ არის')
            if rec.invoice_id.state!='posted':
                raise ValidationError('ინვოისი დადასტურებული არ არის')
            rec.state='checked_out'
            rec.guest_id.message_post(body=f"სტუმარმა დატოვა სასტუმრო. ჯავშანი: <b>{rec.name}</b>, ოთახი: <b>{rec.room_id.room_number}</b>.")
            rec.room_id.sudo().write({'room_status':'available','housekeeping_status':'dirty'})

    def action_cancel(self):
        for rec in self:
            if rec.state !='draft' and rec.state != 'confirmed':
                raise ValidationError('cancel ის გამოძახება დაუშვებელია')
            rec.state='cancelled'
            if rec.room_id:
                rec.room_id.sudo().write({'room_status':'available'})

    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            if vals.get('name','New') == 'New':
                vals['name']=self.env['ir.sequence'].next_by_code('hotel.reservation')
        reservation=super().create(vals_list)
        return reservation

    def action_view_invoice(self):
        self.ensure_one()
        return {
            'name': 'Invoice',
            'type':'ir.actions.act_window',
            'res_model':'account.move',
            'res_id':self.invoice_id.id,
            'view_mode':'form',
            'target':'current'
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
    #invoice creating
    def action_create_invoice(self):
        """ოთახის ინვოისი — შეიძლება შეიქმნას მხოლოდ Check-in-ის შემდეგ (state in checked_in/checked_out),
        რომ სტუმარს Check-out-მდე ჰქონდეს წინასწარი გადახდის საშუალება."""
        for rec in self:
            if rec.state not in ('checked_in', 'checked_out'):
                raise ValidationError('ოთახის ინვოისის შექმნა შესაძლებელია მხოლოდ Check-in-ის შემდეგ')
            if rec.invoice_id:
                raise ValidationError('ამ ჯავშანზე ოთახის ინვოისი უკვე გაცემულია')
            if not rec.guest_id.partner_id:
                raise ValidationError('res.partner-ის გარეშე ინვოისი არ გაიცემა')
            invoice_lines=[]
            if rec.room_id and rec.check_in and rec.check_out:
                day=(rec.check_out -rec.check_in).days
                if day>0:
                    invoice_lines.append((0,0,{
                        'name': f"ოთახის ქირაობა:{rec.room_id.room_number}",
                        'quantity':day,
                        'price_unit':rec.room_id.room_price
                    }))
            # sudo() საჭიროა, რადგან ეს action ხშირად receptionist-ის მიერ Check-in-ის ღილაკიდან
            # გამოიძახება — ინვოისის შექმნას Accounting-ის ცალკე წვდომა არ უნდა ჭირდებოდეს,
            # რადგან ბიზნეს-წესები (state-შემოწმება ზემოთ) უკვე აკონტროლებს ამ მოქმედებას.
            invoice=self.env['account.move'].sudo().create({
                'move_type': 'out_invoice',
                'partner_id': rec.guest_id.partner_id.id,
                'invoice_date':fields.Date.context_today(rec),
                'invoice_line_ids':invoice_lines
            })

            invoice.sudo().action_post()
            rec.invoice_id=invoice.id

            rec.guest_id.message_post(
                body=f"ჯავშანზე <b>{rec.name}</b> შეექმნა ოთახის ინვოისი: <b>{invoice.name}</b> (ჯამი: {invoice.amount_total} GEL)",
                subject='ინვოისის შექმნა',
                message_type='notification',
                subtype_xmlid='mail.mt_note'
            )
        return True

    def action_create_service_invoice(self):
        """დამატებითი სერვისების ინვოისი — ავტომატურად ითვლის ყველა ჯერ არჩაინვოისებელ
        service_line_ids-ს (invoiced=False) და მათზე ცალკე ინვოისს გამოსცემს. თუ დასაინვოისებელი
        არაფერია, არაფერს აკეთებს (ცარიელ ინვოისს არ ქმნის)."""
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

            rec.guest_id.message_post(
                body=f"ჯავშანზე <b>{rec.name}</b> დამატებით სერვისებზე შეიქმნა ინვოისი: "
                     f"<b>{invoice.name}</b> (ჯამი: {invoice.amount_total} GEL)",
                subject='სერვისის ინვოისი',
                message_type='notification',
                subtype_xmlid='mail.mt_note'
            )
        return True
