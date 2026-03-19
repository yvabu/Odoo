from odoo import models,fields,api

class Subjects(models.Model):
    _name="college.subjects"
    _description="Subjects"
    _rec_name="subject_name"

    subject_name=fields.Char()
    teacher_id=fields.Many2one('college.teacher')
    student_ids=fields.Many2many('college.student')


class SubjectSelection(models.Model):
    _name = "college.subject.selection"
    _description = "Subject Selection"
    _rec_name='subject_id'

    # აი აქ ვიყენებთ Many2one-ს, რომელიც  დაინახავს საგნებსის ჩამონათვალს
    subject_id = fields.Many2one('college.subjects', string="აირჩიეთ საგანი")
    #ეს target field აქ იმიტომ დავამატეთ რომ დომეინის მარჯვენა მხარეს არ შეიძლება წერტილის გამოყენება,
     # ანუ ამას ვერ დავწერდით subject_id.teacher_id
    target_teacher_id = fields.Many2one(related='subject_id.teacher_id',string="საგნის რეალური მასწავლებელი")
    teachers_id = fields.Many2one('college.teacher', string="მასწავლებელი",readonly=False,domain="[('id','=',target_teacher_id)]")
    students_ids = fields.Many2many(related='subject_id.student_ids', string="სტუდენტები")