{
    'name': 'Hotel ERP',
    'version': '18.0.1.1',
    'depends': ['base', 'account', 'website', 'portal', 'mail'],
    'sequence': 2,
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/reservation_sequence.xml',
        'data/room_sequence.xml',
        'data/cron.xml',
        'data/cron_auto_check_out.xml',
        'data/system_parameters.xml',
        'views/hotel_room_views.xml',
        'views/hotel_guest_views.xml',
        'views/hotel_reservation_views.xml',
        'views/hotel_service_views.xml',
        'views/website_homepage_templates.xml',
        'views/website_booking_templates.xml',
        'views/website_rooms_templates.xml',
        'views/website_portal_templates.xml',
        'views/hotel_room_details_template.xml',
        'views/hotel_room_card_template.xml',
        'views/hotel_employee_views.xml',
        'views/payment_form_view.xml',
        'views/hotel_reservation_cancel_wizard_views.xml',

        'reports/reservation_report_views.xml',
        'views/hotel_room_menus.xml'
    ],
    'assets': {
        'web.assets_frontend': [
            'hotel_erp/static/src/css/flatpickr_custom.css',
        ],
        'web.assets_backend': [
            'hotel_erp/static/src/js/colored_datepicker.js',
            'hotel_erp/static/src/js/hotel_dashboard.js',
            'hotel_erp/static/src/xml/hotel_dashboard.xml',
            'hotel_erp/static/src/css/hotel_dashboard.css',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3'
}