import logging
import secrets
import werkzeug.urls
from werkzeug.utils import redirect

from odoo import fields, http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.web.controllers.home import Home
from odoo.exceptions import ValidationError
from odoo.http import request
from datetime import timedelta

_logger = logging.getLogger(__name__)


class HotelCustomLogin(Home):

    def _login_redirect(self, uid, redirect=None):
        """ავტორიზაციის შემდეგ მომხმარებლის გადამისამართება /my/dashboard-ზე"""
        user = request.env['res.users'].sudo().browse(uid)

        if not user._is_public():
            return '/my/dashboard'

        return redirect or '/'


class HotelCustomPortal(CustomerPortal):

    @http.route(route=['/my/dashboard', '/my/home'], type='http', auth='user', website=True)
    def account(self, redirect=None, **post):
        """/my/account ან /my-ზე გადასვლისას მომხმარებელი ავტომატურად გადამისამართდება /my/dashboard-ზე"""
        return request.redirect('/my/dashboard')


class HotelReceptionController(http.Controller):

    @http.route(
        route=['/receptionist/guest/create', '/manager/register_guest'],
        type='http',
        auth='user',
        website=True,
        methods=['POST'],
        csrf=True,
    )
    def create_reception_guest(self, **post):
        """ახალი სტუმრის შექმნა ვებიდან"""
        name = post.get('name')
        personal_number = post.get('personal_number') or post.get('identification_id')
        email = post.get('email')
        phone = post.get('phone')
        address = post.get('address')

        if name and personal_number:
            registred_guest = request.env['hotel.guest'].sudo().search([('personal_number', '=', personal_number)],
                                                                       limit=1)
            if registred_guest:
                return redirect('/my/dashboard?error=guest_exists')

            request.env['hotel.guest'].sudo().create({
                'name': name,
                'personal_number': personal_number,
                'email': email,
                'phone': phone,
                'address': address
            })
            return request.redirect('/my/dashboard?success=guest_created')
        return request.redirect('/my/dashboard?error=invalid_data')

    @http.route(
        route=['/receptionist/checkin', '/reception/check_in'],
        type='http',
        auth='user',
        website=True,
        methods=['POST'],
        csrf=True,
    )
    def process_checkin(self, **post):
        """Check-In პროცესი"""
        reservation_id = post.get('reservation_id')
        if reservation_id:
            res = request.env['hotel.reservation'].sudo().browse(int(reservation_id))
            if res.exists():
                try:
                    res.action_check_in()
                except ValidationError as e:
                    return request.redirect(f'/my/dashboard?error={e.args[0]}')
        return request.redirect('/my/dashboard?success=checkin_done')

    @http.route(
        route=['/housekeeping_status/switcher', '/reception/clean_room'],
        type='http',
        auth='user',
        website=True,
        methods=['POST'],
        csrf=True,
    )
    def house_keping_status_switcher(self, **post):
        """ოთახის დასუფთავება"""
        room_id = post.get('room_id')
        if room_id:
            room = request.env['hotel.room'].sudo().browse(int(room_id))
            if room.exists() and room.housekeeping_status in ['dirty', 'maintenance']:
                room.action_set_clean()
                # შენიშვნა: ტემპლეიტი ამოწმებს request.params.get('clean_rooms')-ს
                # (და არა success == 'clean_rooms'-ს), ამიტომ redirect-იც ასე გავასწორეთ.
                return request.redirect('/my/dashboard?clean_rooms=1')
        return request.redirect('/my/dashboard')

    @http.route(
        route=['/receptionist/set_confirm', '/reception/confirm_reservation'],
        type='http',
        auth='user',
        website=True,
        methods=['POST'],
        csrf=True,
    )
    def set_confirm(self, **post):
        """ჯავშნის დადასტურება"""
        reservation_id = post.get('reservation_id')
        if reservation_id:
            res = request.env['hotel.reservation'].sudo().browse(int(reservation_id))
            if res.exists():
                try:
                    res.action_confirm()
                except ValidationError as er:
                    return request.redirect(f'/my/dashboard?error={er.args[0]}')
        return request.redirect('/my/dashboard?success=confirm_done')

    @http.route(
        route=['/receptionist/checkout', '/reception/check_out'],
        type='http',
        auth='user',
        website=True,
        methods=['POST'],
        csrf=True,
    )
    def process_checkout(self, **post):
        """Check-Out პროცესი"""
        reservation_id = post.get('reservation_id')
        if reservation_id:
            res = request.env['hotel.reservation'].sudo().browse(int(reservation_id))
            if res.exists():
                try:
                    res.action_check_out()
                except ValidationError as e:
                    return request.redirect(f'/my/dashboard?error={e.args[0]}')
        return request.redirect('/my/dashboard?success=checkout_done')


class HotelManagerPortal(http.Controller):

    @http.route(
        '/manager/guest/create',
        type='http',
        auth='user',
        website=True,
        methods=['POST'],
        csrf=True,
    )
    def manager_create_guest(self, **post):
        if not request.env.user.has_group('hotel_erp.group_hotel_manager'):
            return request.redirect('/my/dashboard')

        name = post.get('name')
        personal_number = post.get('personal_number') or post.get('identification_id')
        email = post.get('email')
        phone = post.get('phone')
        address = post.get('address')

        if name and personal_number:
            registred_guest = request.env['hotel.guest'].sudo().search([('personal_number', '=', personal_number)],
                                                                       limit=1)
            if registred_guest:
                return redirect('/my/dashboard?error=guest_exists')
            request.env['hotel.guest'].sudo().create({
                'name': name,
                'personal_number': personal_number,
                'email': email,
                'phone': phone,
                'address': address
            })

        return request.redirect('/my/dashboard?success=guest_created')

    @http.route(
        '/manager/payment/create',
        type='http',
        auth='user',
        website=True,
        methods=['POST'],
        csrf=True,
    )
    def manager_create_payment(self, **post):
        """გადახდის რეგისტრაცია Odoo-ს account.payment.register-ის საშუალებით"""
        if not request.env.user.has_group('hotel_erp.group_hotel_manager'):
            return request.redirect('/my/dashboard')

        invoice_id = post.get('invoice_id')
        invoice = request.env['account.move'].sudo().browse(int(invoice_id or 0))

        if not invoice.exists() or invoice.move_type != 'out_invoice':
            return request.redirect('/my/dashboard?error=invalid_invoice')

        if invoice.state != 'posted':
            return request.redirect('/my/dashboard?error=invoice_not_posted')

        try:
            amount = float(post.get('amount') or 0)
        except ValueError:
            amount = 0.0

        if amount <= 0:
            return request.redirect('/my/dashboard?error=invalid_amount')

        payment_method = post.get('payment_method')
        journal_type = 'cash' if payment_method == 'cash' else 'bank'

        journal = request.env['account.journal'].sudo().search(
            [
                ('type', '=', journal_type),
                ('company_id', '=', invoice.company_id.id),
            ],
            limit=1,
        )

        if not journal:
            return request.redirect('/my/dashboard?error=no_journal')

        payment_register = (
            request.env['account.payment.register']
            .sudo()
            .with_context(
                active_model='account.move',
                active_ids=[invoice.id],
            )
            .create({
                'amount': amount,
                'journal_id': journal.id,
                'payment_date': fields.Date.today(),
            })
        )

        payment_register._create_payments()

        return request.redirect('/my/dashboard?success=payment_registered')


class HotelServiceController(http.Controller):

    @http.route('/reservation/add_service', type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def add_service_to_reservation(self, **post):
        """სერვისის დამატება არსებულ ჯავშანზე"""
        reservation_id = post.get('reservation_id')
        service_id = post.get('service_id')
        quantity = int(post.get('quantity') or 1)

        if reservation_id and service_id:
            reservation = request.env['hotel.reservation'].sudo().browse(int(reservation_id))
            service = request.env['hotel.service'].sudo().browse(int(service_id))

            if reservation.exists() and service.exists():
                if reservation.state in ('checked_out', 'cancelled'):
                    return request.redirect('/my/dashboard?error=service_failed')

                if hasattr(reservation, 'action_add_service'):
                    reservation.action_add_service(service.id, quantity)
                else:
                    # hotel.reservation.line მოდელში ველს ჰქვია 'quantity' (და არა 'qty'),
                    # ასევე price_unit სერვისის ფასიდან უნდა შემოვიტანოთ, რომ
                    # total_price/price_subtotal სწორად დაითვალოს.
                    request.env['hotel.reservation.line'].sudo().create({
                        'reservation_id': reservation.id,
                        'service_id': service.id,
                        'quantity': quantity,
                        'price_unit': service.price,
                    })

                # 🔑 რეალურ დროში ინვოისირება: თუ სტუმარი უკვე Check-in-ის შემდეგაა
                # (checked_in), დამატებული სერვისი მაშინვე ინვოისდება, რომ
                # დაუყოვნებლივ გადასახდელი გახდეს (წინასწარი გადახდის საშუალება
                # stay-ის განმავლობაშივე, არა მხოლოდ Check-out-ზე).
                # Check-in-ის მდგომარეობაში guest_id.partner_id უკვე გარანტირებულია
                # (action_create_invoice ოთახის ინვოისისთვის ამას მოითხოვდა Check-in-ზე),
                # ამიტომ ეს გამოძახება უსაფრთხოა.
                if reservation.state == 'checked_in':
                    try:
                        reservation.action_create_service_invoice()
                    except ValidationError:
                        # თუ რაიმე მიზეზით ინვოისის შექმნა ახლა ვერ მოხერხდა,
                        # სერვისი მაინც დამატებულია და Check-out-ის დროს
                        # action_create_service_invoice() ისედაც ავტომატურად
                        # დაინვოისებს ყველა ჯერ არჩაინვოისებელ ხაზს (safety net).
                        _logger.exception(
                            'სერვისის დაუყოვნებელი ინვოისირება ვერ მოხერხდა ჯავშანზე %s', reservation.id
                        )

                return request.redirect('/my/dashboard?success=service_added')

        return request.redirect('/my/dashboard?error=service_failed')

    @http.route('/manager/create_service', type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def manager_create_service(self, **post):
        """ახალი სერვისის შექმნა სისტემაში მენეჯერის მიერ"""
        if not request.env.user.has_group('hotel_erp.group_hotel_manager'):
            return request.redirect('/my/dashboard')

        name = post.get('name')
        price = float(post.get('price') or 0.0)

        if name and price > 0:
            request.env['hotel.service'].sudo().create({
                'name': name,
                'price': price,
            })
            return request.redirect('/my/dashboard?success=service_created')

        return request.redirect('/my/dashboard?error=invalid_service_data')


class HotelWebsite(http.Controller):

    @http.route('/', type='http', auth='public', website=True)
    def home(self, **kwargs):
        rooms = request.env['hotel.room'].sudo().search([('housekeeping_status', '=', 'clean')])
        return request.render('hotel_erp.hotel_homepage', {'rooms': rooms})


class HotelRoomsWebsite(http.Controller):

    @http.route('/rooms', type='http', auth='public', website=True)
    def hotel_room(self, check_in=None, check_out=None, **kwargs):
        domain = [('active', '=', True)]
        ci = co = None
        date_error = None
        if check_in and check_out:
            try:
                ci = fields.Date.from_string(check_in)
                co = fields.Date.from_string(check_out)
            except ValueError:
                date_error = 'invalid_date'

            if ci and co:
                if co <= ci:
                    date_error = 'checkout_before_checkin'
                else:
                    overlapping = request.env['hotel.reservation'].sudo().search([
                        ('check_in', '<', co),
                        ('check_out', '>', ci),
                        ('state', '!=', 'cancelled'),
                    ])
                    booked_room_ids = overlapping.mapped('room_id').ids
                    if booked_room_ids:
                        domain.append(('id', 'not in', booked_room_ids))

        hotel_rooms = request.env['hotel.room'].sudo().search(domain)

        return request.render(
            'hotel_erp.hotel_rooms_page',
            {
                'hotel_rooms': hotel_rooms,
                'check_in': check_in or '',
                'check_out': check_out or '',
                'filtered': bool(ci and co and not date_error),
                'date_error': date_error,
            },
        )

    @http.route('/room/<int:room_id>', type='http', auth='public', website=True)
    def room_details(self, room_id, check_in=None, check_out=None, **kwargs):
        room = request.env['hotel.room'].sudo().browse(room_id)
        if not room.exists():
            return request.redirect('/rooms')

        return request.render(
            'hotel_erp.hotel_room_details_page',
            {
                'room': room,
                'check_in': check_in or '',
                'check_out': check_out or '',
            },
        )


class HotelRoomController(http.Controller):

    @http.route('/hotel/get_booked_dates', type='json', auth='public', website=True)
    def get_booked_dates(self, room_id):
        if not room_id:
            return []

        reservations = request.env['hotel.reservation'].sudo().search([
            ('room_id', '=', int(room_id)),
            ('state', '!=', 'cancelled'),
        ])

        disabled_dates = []
        for res in reservations:
            current_date = res.check_in
            while current_date < res.check_out:
                disabled_dates.append(current_date.strftime('%Y-%m-%d'))
                current_date += timedelta(days=1)

        return disabled_dates


class BookingForm(http.Controller):

    @http.route('/booking', type='http', auth='public', website=True)
    def booking_form(self, room_id=None, check_in=None, check_out=None, **kwargs):
        user = request.env.user
        is_public = user._is_public()
        is_staff = (not is_public) and (
                user.has_group('hotel_erp.group_hotel_user')
                or user.has_group('hotel_erp.group_hotel_manager')
        )
        is_self_service = (not is_public) and (not is_staff)

        domain = [('active', '=', True)]
        ci = co = None
        if check_in and check_out:
            try:
                ci = fields.Date.from_string(check_in)
                co = fields.Date.from_string(check_out)
            except ValueError:
                ci = co = None
            if ci and co and co > ci:
                overlapping = request.env['hotel.reservation'].sudo().search([
                    ('check_in', '<', co),
                    ('check_out', '>', ci),
                    ('state', '!=', 'cancelled'),
                ])
                booked_room_ids = overlapping.mapped('room_id').ids
                if booked_room_ids:
                    domain.append(('id', 'not in', booked_room_ids))

        rooms = request.env['hotel.room'].sudo().search(domain)
        selected_room = False
        if room_id:
            selected_room = request.env['hotel.room'].sudo().browse(int(room_id))

        return request.render(
            'hotel_erp.hotel_booking_form_page',
            {
                'rooms': rooms,
                'selected_room': selected_room,
                'check_in': check_in or '',
                'check_out': check_out or '',
                'is_public': is_public,
                'is_staff': is_staff,
                'is_self_service': is_self_service,
                'user': user,
            },
        )

    @http.route('/booking/submit', type='http', auth='public', website=True, methods=['POST'], csrf=True)
    def booking_submit(self, **post):
        guest_name = post.get('guest_name')
        email = post.get('email')
        phone = post.get('phone')
        personal_number = post.get('personal_number')
        room_id = int(post.get('room_id')) if post.get('room_id') else False
        check_in = post.get('check_in')
        check_out = post.get('check_out')
        address = post.get('address')

        current_user = request.env.user
        is_public = current_user._is_public()
        is_staff = (not is_public) and (
                current_user.has_group('hotel_erp.group_hotel_user')
                or current_user.has_group('hotel_erp.group_hotel_manager')
        )

        partner = False
        newly_registered = False

        if is_public:
            if not email:
                return request.redirect(f'/booking?room_id={room_id or ""}&error=email_required')

            existing_user = request.env['res.users'].sudo().search([('login', '=', email)], limit=1)
            if existing_user:
                redirect_target = '/booking'
                params = [
                    p for p in [
                        f'room_id={room_id}' if room_id else '',
                        f'check_in={check_in}' if check_in else '',
                        f'check_out={check_out}' if check_out else '',
                    ] if p
                ]
                if params:
                    redirect_target += '?' + '&'.join(params)
                return request.redirect(f'/web/login?redirect={werkzeug.urls.url_quote(redirect_target)}')

            new_partner = request.env['res.partner'].sudo().create({
                'name': guest_name,
                'email': email,
                'phone': phone,
                'street': address,
            })
            random_password = secrets.token_urlsafe(12)
            new_user = request.env['res.users'].sudo().create({
                'name': guest_name,
                'login': email,
                'email': email,
                'partner_id': new_partner.id,
                'groups_id': [(4, request.env.ref('base.group_portal').id)],
                'password': random_password,
            })
            request.env.cr.commit()
            credential = {
                'login': email,
                'password': random_password,
                'type': 'password',
            }
            request.session.authenticate(request.db, credential)

            try:
                new_user.sudo().action_reset_password()
                signup_url = new_user.sudo().generate_signup_url()
                if signup_url:
                    _logger.info('🔑 [HOTEL ERP] Password set-up ბმული %s-სთვის: %s', email, signup_url)
            except Exception:
                _logger.exception('Password reset email-ის გაგზავნა ვერ მოხერხდა %s-სთვის', email)

            partner = new_user.partner_id
            newly_registered = True

        elif is_staff:
            partner = False

        else:
            user = current_user
            partner = user.partner_id
            guest_name = guest_name or user.name
            email = email or user.email
            phone = phone or partner.phone
            partner.sudo().write({
                'phone': phone or partner.phone,
                'street': address or partner.street,
            })

        guest = request.env['hotel.guest'].sudo().search([('personal_number', '=', personal_number)], limit=1)
        if not guest:
            guest_vals = {
                'name': guest_name,
                'personal_number': personal_number,
                'phone': phone,
                'email': email,
                'address': address,
            }
            if partner:
                guest_vals['partner_id'] = partner.id
            if newly_registered:
                guest_vals['user_id'] = partner.user_ids[:1].id
            guest = request.env['hotel.guest'].sudo().create(guest_vals)
        else:
            update_vals = {'phone': phone, 'email': email}
            if partner and not guest.partner_id:
                update_vals['partner_id'] = partner.id
            if newly_registered and not guest.user_id:
                update_vals['user_id'] = partner.user_ids[:1].id
            guest.sudo().write(update_vals)

        reservation = request.env['hotel.reservation'].sudo().create({
            'guest_id': guest.id,
            'room_id': room_id,
            'check_in': check_in,
            'check_out': check_out,
            'state': 'draft',
        })

        if newly_registered:
            return request.redirect('/my/dashboard?success=account_created')

        if is_staff:
            return request.redirect('/my/dashboard?success=booking_created')

        return request.render(
            'hotel_erp.hotel_booking_success_page',
            {
                'reservation': reservation,
            },
        )


class HotelPortal(http.Controller):

    @http.route('/my/dashboard', type='http', auth='user', website=True)
    def my_dashboard(self, success=None, **kwargs):
        user = request.env.user
        available_services = request.env['hotel.service'].sudo().search([])

        # 1. MANAGER DASHBOARD
        if user.has_group('hotel_erp.group_hotel_manager'):
            reservations = request.env['hotel.reservation'].sudo().search([])
            rooms = request.env['hotel.room'].sudo().search([])
            guests = request.env['hotel.guest'].sudo().search([])

            invoices = reservations.mapped('invoice_id') | reservations.mapped('service_invoice_ids')
            payments = invoices.mapped('payment_ids')

            return request.render(
                'hotel_erp.portal_my_dashboard',
                {
                    'reservations': reservations,
                    'rooms': rooms,
                    'guests': guests,
                    'invoices': invoices,
                    'payments': payments,
                    'available_services': available_services,
                    'role': 'manager',
                    'success': success,
                },
            )

        # 2. RECEPTIONIST DASHBOARD
        elif user.has_group('hotel_erp.group_hotel_user'):
            pending_reservations = request.env['hotel.reservation'].sudo().search(
                [('state', 'in', ['draft', 'confirmed'])])
            checked_in_reservations = request.env['hotel.reservation'].sudo().search([('state', '=', 'checked_in')])
            dirty_rooms = request.env['hotel.room'].sudo().search(
                [('housekeeping_status', 'in', ['dirty', 'maintenance'])])

            return request.render(
                'hotel_erp.portal_my_dashboard',
                {
                    # ტემპლეიტში (portal_my_dashboard) receptionist-ის განშტოებაში
                    # იხმარება 'checkins' და 'active_reservations' სახელები —
                    # ამიტომ იმავე მნიშვნელობებს ვაბრუნებთ ამ key-ებითაც, რომ ცხრილებმა
                    # იმუშაონ (ძველი key-ებიც ვტოვებთ თავსებადობისთვის).
                    'pending_reservations': pending_reservations,
                    'checked_in_reservations': checked_in_reservations,
                    'checkins': pending_reservations,
                    'active_reservations': checked_in_reservations,
                    'dirty_rooms': dirty_rooms,
                    'available_services': available_services,
                    'role': 'receptionist',
                    'success': success,
                },
            )

        # 3. GUEST DASHBOARD
        else:
            guest = request.env['hotel.guest'].sudo().search(
                [
                    '|',
                    ('partner_id', '=', user.partner_id.id),
                    ('email', '=', user.email),
                ],
                limit=1,
            )

            my_reservations = request.env['hotel.reservation']
            invoices = request.env['account.move']
            payments = request.env['account.payment']
            show_checkin_notice = False

            if guest:
                my_reservations = request.env['hotel.reservation'].sudo().search(
                    [
                        ('guest_id', '=', guest.id),
                        ('state', '!=', 'cancelled'),
                    ]
                )

                checked_in_reservations = my_reservations.filtered(lambda r: r.state in ['checked_in', 'done'])

                if checked_in_reservations:
                    invoices = checked_in_reservations.mapped('invoice_id') | checked_in_reservations.mapped(
                        'service_invoice_ids')
                    payments = invoices.mapped('payment_ids')
                elif my_reservations:
                    show_checkin_notice = True

            return request.render(
                'hotel_erp.portal_my_dashboard',
                {
                    # ტემპლეიტის guest-ის განშტოებაში იხმარება 'reservations' და
                    # 'invoices' სახელები — ამიტომ იმავე მნიშვნელობებს ვაბრუნებთ
                    # ამ key-ებითაც (ძველი key-ებიც ვტოვებთ თავსებადობისთვის).
                    'my_reservations': my_reservations,
                    'my_invoices': invoices,
                    'reservations': my_reservations,
                    'invoices': invoices,
                    'payments': payments,
                    'available_services': available_services,
                    'show_checkin_notice': show_checkin_notice,
                    'role': 'guest',
                    'success': success,
                },
            )

    @http.route('/dashboard/guest/create', type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def dashboard_create_guest(self, **post):
        if request.env.user.has_group('hotel_erp.group_hotel_manager') or request.env.user.has_group(
                'hotel_erp.group_hotel_user'):
            request.env['hotel.guest'].sudo().create({
                'name': post.get('name'),
                'email': post.get('email'),
                'phone': post.get('phone'),
                'personal_number': post.get('personal_number') or post.get('identification_id'),
            })
            return request.redirect('/my/dashboard?success=guest_created')
        return request.redirect('/my/dashboard')

    @http.route('/dashboard/reservation/create', type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def dashboard_create_reservation(self, **post):
        if request.env.user.has_group('hotel_erp.group_hotel_manager') or request.env.user.has_group(
                'hotel_erp.group_hotel_user'):
            guest_id = post.get('guest_id')
            room_id = post.get('room_id')
            check_in = post.get('check_in')
            check_out = post.get('check_out')

            if guest_id and room_id and check_in and check_out:
                request.env['hotel.reservation'].sudo().create({
                    'guest_id': int(guest_id),
                    'room_id': int(room_id),
                    'check_in': check_in,
                    'check_out': check_out,
                    'state': 'draft',
                })
                return request.redirect('/my/dashboard?success=booking_created')
        return request.redirect('/my/dashboard')

    @http.route('/dashboard/payment/register', type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def dashboard_register_payment(self, **post):
        if request.env.user.has_group('hotel_erp.group_hotel_manager'):
            invoice_id = post.get('invoice_id')
            amount = post.get('amount')
            invoice = request.env['account.move'].sudo().browse(int(invoice_id or 0))

            if invoice.exists() and amount:
                payment_register = (
                    request.env['account.payment.register']
                    .sudo()
                    .with_context(active_model='account.move', active_ids=[invoice.id])
                    .create({'amount': float(amount)})
                )
                payment_register._create_payments()
                return request.redirect('/my/dashboard?success=payment_registered')
        return request.redirect('/my/dashboard')

    @http.route('/my/reservation/cancel', type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def cancel_reservation(self, reservation_id=None, **kwargs):
        if reservation_id:
            reservation = request.env['hotel.reservation'].sudo().browse(int(reservation_id))
            if reservation.exists() and (
                    reservation.guest_id.email == request.env.user.email
                    or reservation.guest_id.partner_id.id == request.env.user.partner_id.id
            ):
                reservation.write({'state': 'cancelled'})
                return request.redirect('/my/dashboard?success=booking_cancelled')
        return request.redirect('/my/dashboard')