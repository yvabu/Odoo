from odoo import http
from odoo.http import request
# შემოგვაქვს პორტალის კონტროლერი გადამისამართებისთვის
from odoo.addons.portal.controllers.portal import CustomerPortal





class CollegeHome(http.Controller):
    @http.route('/collegehome', type='http', auth='user', website=True)
    def index(self, **kw):
        user = request.env.user

        # ვამოწმებთ არის თუ არა შემსვლელი სტუდენტი
        student = request.env['college.student'].sudo().search([('user_id', '=', user.id)], limit=1)
        if student:
            marks = request.env['college.mark'].sudo().search([('student_id', '=', student.id)])
            return request.render('college_erp.student_dashboard_main', {
                'student': student,
                'marks': marks,
            })

        # ვამოწმებთ არის თუ არა შემსვლელი მასწავლებელი
        teacher = request.env['college.teacher'].sudo().search([('user_id', '=', user.id)], limit=1)
        if teacher:
            subjects = request.env['college.subjects'].sudo().search([('teacher_id', '=', teacher.id)])
            return request.render('college_erp.teacher_dashboard', {
                'teacher': teacher,
                'subjects': subjects
            })

        return request.render('website.homepage')


class StudentReportController(http.Controller):
    @http.route(['/student/download/report/<int:student_id>'], type='http', auth="user", website=True)
    def download_pdf_report(self, student_id, **kw):
        student = request.env['college.student'].sudo().browse(student_id)

        if not student.exists() or student.user_id.id != request.env.user.id:
            return request.render('website.403')

        report_name = 'college_erp.report_student_template'

        # Odoo 18-ის უსაფრთხო PDF გენერაცია სუპერ-იუზერის კონტექსტით
        report_sudo = request.env['ir.actions.report'].sudo()
        pdf_content, _ = report_sudo._render_qweb_pdf(report_name, [student.id])

        pdf_http_headers = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf_content)),
            ('Content-Disposition', 'attachment; filename="Academic_Record.pdf"'),
        ]
        return request.make_response(pdf_content, headers=pdf_http_headers)


class TeacherMarks(http.Controller):
    @http.route('/teacher_marks/<int:mark_id>', type='http', auth='user', website=True, methods=['GET', 'POST'],
                csrf=True)
    def teacher_mark_web(self, mark_id, **kw):
        mark = request.env['college.mark'].sudo().browse(mark_id)
        if not mark.exists() or mark.teacher_id.user_id.id != request.env.user.id:
            return request.render('website.403')

        if request.httprequest.method == 'POST':
            vals = {
                'shualeduri': float(kw.get('shualeduri') or 0),
                'final': float(kw.get('final') or 0),
                'comment': kw.get('comment')
            }
            for i in range(1, 11):
                vals[f'w{i}'] = float(kw.get(f'w{i}') or 0)

            mark.write(vals)
            return request.redirect(f'/teacher_marks/{mark_id}?success=1')

        return request.render('college_erp.teacher_mark_web', {'mark': mark})


class TeacherActions(http.Controller):
    @http.route('/teacher/subject/<int:subject_id>', type='http', auth='user', website=True)
    def teacher_subject_students(self, subject_id, **kw):
        teacher = request.env['college.teacher'].sudo().search([('user_id', '=', request.env.user.id)], limit=1)
        if not teacher:
            return request.render('website.403')

        marks = request.env['college.mark'].sudo().search([
            ('subject_id', '=', subject_id),
            ('teacher_id', '=', teacher.id)
        ])
        subject = request.env['college.subjects'].sudo().browse(subject_id)
        return request.render('college_erp.teacher_students_list', {'subject': subject, 'marks': marks})


class MarkStudent(http.Controller):
    @http.route('/student_marks/<int:mark_id>', type='http', auth='user', website=True)
    def student_mark_det(self, mark_id, **kw):
        mark = request.env['college.mark'].sudo().browse(mark_id)

        if not mark.exists() or mark.student_id.user_id.id != request.env.user.id:
            return request.render('website.403')

        return request.render('college_erp.student_marks_template', {
            'mark': mark,
        })