{
    'name': 'Hotel ERP',
    'version': '18.0.1.1',
    'depends': ['base','account','website','portal','mail'],
    'sequence':2,
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/reservation_sequence.xml',
        'data/room_sequence.xml',
        'views/hotel_room_views.xml',
        'views/hotel_guest_views.xml',
        'views/hotel_reservation_views.xml',
        'views/hotel_service_views.xml',
        'views/website_homepage_templates.xml',
        'views/website_booking_templates.xml',
        'views/website_rooms_templates.xml',
        'views/website_portal_templates.xml',
        'views/hotel_room_details_template.xml',
        'views/hotel_employee_views.xml',
        'reports/reservation_report_views.xml',
        'views/hotel_room_menus.xml'
    ],
    'assets': {
         'web.assets_frontend': [
             'hotel_erp/static/src/css/flatpickr_custom.css',
         ],
        'web.assets_backend':[
            'hotel_erp/static/src/js/colored_datepicker.js',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3'
}