import datetime
from odoo import models, fields, api
from odoo.exceptions import AccessError


class HotelDashboard(models.AbstractModel):
    _name = 'hotel.dashboard'
    _description = 'Hotel Dashboard'

    @api.model
    def get_dashboard_data(self, date_from=None, date_to=None):
        user = self.env.user
        is_manager = user.has_group('hotel_erp.group_hotel_manager')
        is_receptionist = user.has_group('hotel_erp.group_hotel_user')
        is_admin=user.has_group('base.group_system')
        if not (is_manager or is_receptionist or is_admin):
            raise AccessError("The dashboard is available only to hotel staff.")

        today = fields.Date.context_today(self)
        if not date_from:
            date_from = today.replace(day=1)
        else:
            date_from = fields.Date.to_date(date_from)

        if not date_to:
            next_month = today.replace(day=28) + datetime.timedelta(days=4)
            date_to = next_month - datetime.timedelta(days=next_month.day)
        else:
            date_to = fields.Date.to_date(date_to)

        env = self.sudo().env

        result = {
            'currency_id': self.env.company.currency_id.id,
            'is_manager': is_manager,
            'date_from': fields.Date.to_string(date_from),
            'date_to': fields.Date.to_string(date_to),
            'is_receptionist':is_receptionist,
            'is_admin':is_admin,
        }

        result.update(self._get_room_data())
        result.update(self._get_reservation_data(env, today, date_from, date_to))
        if is_manager or is_receptionist or is_admin:
            result.update(self._get_finance_data(env, date_from, date_to))

        return result

    def _get_room_data(self):
        room = self.sudo().env['hotel.room']
        occupied = room.search([('reservation_ids.state', '=', 'checked_in')])
        occupied_rooms_count = len(occupied)

        available_domain=[('room_status','=', 'available'),('id','not in',occupied.ids)]
        available_rooms = room.search_count(available_domain)

        return {
            'occupied_rooms': occupied_rooms_count,
            'available_rooms': available_rooms,
            'occupied_rooms_domain':[('id','in',occupied.ids)],
            'available_rooms_domain':available_domain
        }

    def _get_reservation_data(self, env, today, date_from, date_to):
        ReservationModel = env['hotel.reservation']
        domain = [('check_in', '>=', date_from), ('check_in', '<=', date_to)]
        active_states = ['pending', 'confirmed', 'checked_in']

        rows = ReservationModel._read_group(domain + [('state', 'in', active_states)], groupby=['state'], aggregates=['__count'])
        counted = {state: count for state, count in rows}
        by_state = {s: counted.get(s, 0) for s in active_states}


        checkins_today_domain=[('check_in','=',today),('state','=','checked_in')]
        checkouts_today_domain=[('checked_out_at','>=',fields.Datetime.to_datetime(today)),('checked_out_at','<=',fields.Datetime.to_datetime(today + datetime.timedelta(days=1)))]
        checkins_today = ReservationModel.search_count(checkins_today_domain)
        checkouts_today = ReservationModel.with_context(active_test=False).search_count(checkouts_today_domain)
        guest_total = env['hotel.guest'].search_count([])

        return {
            'reservations_total': sum(by_state.values()),
            'reservations_by_state': by_state,
            'checkins_today': checkins_today,
            'checkouts_today': checkouts_today,
            'guests_total': guest_total,
            'checkins_today_domain': checkins_today_domain,
            'checkouts_today_domain': checkouts_today_domain,
        }

    def _get_finance_data(self, env, date_from, date_to):
        Move = env['account.move']
        Payment = env['account.payment']
        Reservation = env['hotel.reservation'].with_context(active_test=False)
        currency = env.company.currency_id

        # 1. შემოსავლები (Revenue) - ფილტრაცია ჯავშნების Check-in თარიღით
        reservations = Reservation.search([('check_in', '>=', date_from), ('check_in', '<=', date_to),('state','!=','cancelled')])
        hotel_invoice_ids = set(reservations.invoice_id.ids) | set(reservations.service_invoice_ids.ids)

        revenue_domain=[
            ('id','in',list(hotel_invoice_ids)),
            ('move_type','in',['out_invoice','out_refund']),
            ('state','=','posted'),
        ]
        revenue_rows = Move._read_group(revenue_domain, aggregates=['amount_untaxed_signed:sum'])

        revenue = (revenue_rows[0][0] or 0.0) if revenue_rows else 0.0

        # 2. ხარჯები (Expenses) - ფილტრაცია ინვოისის თარიღით

        expense_domain=[
            ('move_type','in',['in_invoice','in_refund']),
            ('state','=','posted'),
            ('invoice_date','>=',date_from),
            ('invoice_date','<=',date_to),
        ]

        expense_rows = Move._read_group(expense_domain, aggregates=['amount_untaxed_signed:sum'])

        expense_total = (expense_rows[0][0] or 0.0) if expense_rows else 0.0
        expenses = -expense_total if expense_total else 0.0

        # 3. გადახდები (Payments) - ფილტრაცია გადახდის თარიღით

        payment_domain=[
            ('payment_type','=','inbound'),
            ('reservation_id','!=',False),
            ('reservation_id.state','!=','cancelled'),
            ('state','in',['in_process','paid','posted']),
            ('date','>=', date_from),
            ('date','<=', date_to),
        ]

        payments = Payment.search(payment_domain)

        if 'amount_company_currency_signed' in Payment._fields:
            paid_amount = sum(payments.mapped('amount_company_currency_signed'))
        else:
            paid_amount = sum(payments.mapped('amount'))

        net_profit = revenue - expenses

        revenue_ids=Move.search(revenue_domain).ids
        expense_ids=Move.search(expense_domain).ids
        profit_domain=[('id','in',revenue_ids + expense_ids)]

        return {
            'revenue': currency.round(revenue),
            'expenses': currency.round(expenses),
            'net_profit': currency.round(net_profit),
            'paid_amount': currency.round(paid_amount),
            'net_profit_domain': profit_domain,
            'revenue_domain': revenue_domain,
            'expenses_domain':expense_domain,
            'paid_amount_domain': payment_domain
        }