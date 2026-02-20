{
    'name': "College ERP",
    'version': "18.0.1.1",
    'license': "LGPL-3",
    'summary': """An erp for college education""",
    'description': """From students administration to exam,this covers all aspects of college administration""",
    'author': "Saba Kobalia",
    'website': "www.sabakobalia.com",
    'category': "education",
    'sequence': 1,
    'depends': ["base"],
    'data':[
    "security/college_erp_security.xml",
    "security/ir.model.access.csv",
    "views/college_student_view.xml",
    "views/female_student_view.xml",
    "views/male_student_view.xml",
    "views/first_course_view.xml",
    "views/college_erp_menus.xml",
    ],
    'application': True,
    'auto_install': True,
    'installable': True,


}