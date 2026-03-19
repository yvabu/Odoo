from odoo import http
from odoo.http import request



class CollegeHome(http.Controller):

    @http.route('/', type='http', auth='user', website=True)
    def index(self, **kw):
        user = request.env.user
        # ვამოწმებთ არის თუ არა შემსვლელი სტუდენტი
        student = request.env['college.student'].sudo().search([('user_id', '=', user.id)], limit=1)
        if student:
            # თუ სტუდენტია, ამოვუღოთ მისი ნიშნები
            marks = request.env['college.mark'].sudo().search([('student_id', '=', student.id)])
            return request.render('college_erp.student_dashboard_main', {
                'student': student,
                'marks': marks,
            })
        # თუ სტუდენტი არაა (მაგ: სტუმარია), ვუჩვენოთ სტანდარტული საიტი
        teacher = request.env['college.teacher'].sudo().search([('user_id', '=', user.id)], limit=1)
        if teacher:
            # ვიღებთ საგნებს, რომლებსაც ეს მასწავლებელი ასწავლის
            subjects = request.env['college.subjects'].sudo().search([('teacher_id', '=', teacher.id)])
            return request.render('college_erp.teacher_dashboard', {
                'teacher': teacher,
                'subjects': subjects
            })
        return request.render('website.homepage')
class TeacherMarks(http.Controller):
    @http.route('/teacher_marks/<int:mark_id>', type='http', auth='user', website=True, methods=['GET', 'POST'],csrf=True)
    def teacher_mark_web(self, mark_id, **kw):
        mark = request.env['college.mark'].sudo().browse(mark_id)
        if not mark.exists() or mark.teacher_id.user_id.id != request.env.user.id:
            return request.render('website.403')

        if request.httprequest.method == 'POST':
            # მონაცემების შენახვა
            vals = {
                'shualeduri': float(kw.get('shualeduri') or 0),
                'final': float(kw.get('final') or 0),
                'comment': kw.get('comment')
            }
            # კვირების შენახვა ციკლით
            for i in range(1, 11):
                vals[f'w{i}'] = float(kw.get(f'w{i}') or 0)

            mark.write(vals)
            return request.redirect(f'/teacher_marks/{mark_id}?success=1')

        return request.render('college_erp.teacher_mark_web', {'mark': mark})

class TeacherActions(http.Controller):
    # 1. კონკრეტული საგნის სტუდენტების სია
    @http.route('/teacher/subject/<int:subject_id>', type='http', auth='user', website=True)
    def teacher_subject_students(self, subject_id, **kw):
        teacher = request.env['college.teacher'].sudo().search([('user_id', '=', request.env.user.id)], limit=1)
        marks = request.env['college.mark'].sudo().search([
            ('subject_id', '=', subject_id),
            ('teacher_id', '=', teacher.id)
        ])
        subject = request.env['college.subjects'].sudo().browse(subject_id)
        return request.render('college_erp.teacher_students_list', {'subject': subject, 'marks': marks})
class MarkStudent(http.Controller):
    @http.route('/student_marks/<int:mark_id>', type='http', auth='user', website=True)
    def student_mark_det(self, mark_id, **kw):
        # sudo() აქ არის გადამწყვეტი - ის უფლებებს "უგულებელყოფს" მხოლოდ ამ კოდისთვის
        mark = request.env['college.mark'].sudo().browse(mark_id)

        # უსაფრთხოების ფილტრი: რომ სტუდენტმა სხვისი ID-ის ჩაწერით სხვისი ნიშნები არ ნახოს
        if mark.student_id.user_id.id != request.env.user.id:
            return request.render('website.403')  # თუ სხვისია, ვუბლოკავთ წვდომას

        return request.render('college_erp.student_marks_template', {
            'mark': mark,
        })

