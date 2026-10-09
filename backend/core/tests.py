from io import BytesIO
import tempfile
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import OperationalError
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from rest_framework.test import APITestCase

from datetime import timedelta
from unittest.mock import patch

from .models import (
    Assignment,
    AssignmentSubmission,
    Attendance,
    CalendarEvent,
    Course,
    CourseEnrollment,
    Conversation,
    Exam,
    ExamQuestion,
    Grade,
    Lesson,
    Message,
    ProfilePhoto,
    Quiz,
    Question,
    StudentParent,
    Subject,
)

User = get_user_model()


class EDUCOREAPITests(APITestCase):
    def setUp(self):
        self.temp_media = tempfile.TemporaryDirectory()
        self.media_settings = override_settings(MEDIA_ROOT=self.temp_media.name)
        self.media_settings.enable()
        self.addCleanup(self.temp_media.cleanup)
        self.addCleanup(self.media_settings.disable)
        self.teacher = User.objects.create_user(
            username="teacher",
            email="teacher@example.com",
            password="StrongTeacherPass!481",
            role=User.Role.TEACHER,
        )
        self.subject = Subject.objects.create(name="Mathematics", slug="mathematics")
        self.course = Course.objects.create(
            title="Algebra",
            slug="algebra",
            subject=self.subject,
            teacher=self.teacher,
            status=Course.Status.PUBLISHED,
        )
        self.lesson = Lesson.objects.create(course=self.course, title="Equations", order=1)
        self.student = User.objects.create_user(
            username="student",
            email="student@example.com",
            password="StrongStudentPass!481",
            role=User.Role.STUDENT,
        )
        self.parent = User.objects.create_user(
            username="parent",
            email="parent@example.com",
            password="StrongParentPass!481",
            role=User.Role.PARENT,
        )
        self.other_student = User.objects.create_user(
            username="other-student",
            email="other-student@example.com",
            password="StrongOtherPass!481",
            role=User.Role.STUDENT,
        )
        StudentParent.objects.create(student=self.student, parent=self.parent)

    @staticmethod
    def make_test_image(name="avatar.png", image_format="PNG"):
        stream = BytesIO()
        Image.new("RGB", (24, 24), color=(96, 80, 180)).save(stream, format=image_format)
        return SimpleUploadedFile(
            name,
            stream.getvalue(),
            content_type=f"image/{image_format.lower()}",
        )

    def test_registration_cannot_self_assign_privileged_roles(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "new-user",
                "email": "new@example.com",
                "password": "N!ne-Rivers-72-Dawn",
                "role": "admin",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(username="new-user").exists())

    def test_health_check_reports_database_readiness(self):
        healthy = self.client.get(reverse("health-check"))
        self.assertEqual(healthy.status_code, 200)
        self.assertEqual(healthy.data["database"], "available")

        with patch("core.views.connection.ensure_connection", side_effect=OperationalError("database offline")):
            unhealthy = self.client.get(reverse("health-check"))
        self.assertEqual(unhealthy.status_code, 503)
        self.assertEqual(unhealthy.data["database"], "unavailable")

    def test_superuser_gets_administrator_role(self):
        administrator = User.objects.create_superuser(
            username="site-admin",
            email="site-admin@example.com",
            password="StrongAdminPassword!481",
        )
        self.assertEqual(administrator.role, User.Role.ADMIN)

    def test_only_administrators_can_manage_accounts_from_the_portal(self):
        self.client.force_authenticate(self.teacher)
        self.assertEqual(self.client.get(reverse("admin-user-list")).status_code, 403)

        administrator = User.objects.create_user(
            username="portal-admin",
            email="portal-admin@example.com",
            password="StrongAdminPassword!925",
            role=User.Role.ADMIN,
        )
        self.client.force_authenticate(administrator)
        response = self.client.post(
            reverse("admin-user-list"),
            {
                "username": "new-teacher",
                "email": "new-teacher@example.com",
                "first_name": "New",
                "last_name": "Teacher",
                "role": User.Role.TEACHER,
                "password": "N!ne-Rivers-72-Dawn",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["role"], User.Role.TEACHER)
        self.assertNotIn("password", response.data)
        created_teacher = User.objects.get(username="new-teacher")
        self.assertTrue(created_teacher.check_password("N!ne-Rivers-72-Dawn"))
        self.assertTrue(hasattr(created_teacher, "teacher_profile"))

    def test_students_cannot_use_admin_account_management_api(self):
        self.client.force_authenticate(self.student)
        response = self.client.post(
            reverse("admin-user-list"),
            {
                "username": "attempted-admin",
                "email": "attempted-admin@example.com",
                "role": User.Role.ADMIN,
                "password": "N!ne-Rivers-72-Dawn",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(User.objects.filter(username="attempted-admin").exists())

    def test_login_returns_token_and_current_user(self):
        token_response = self.client.post(
            reverse("token-obtain"),
            {"username": self.student.username, "password": "StrongStudentPass!481"},
            format="json",
        )
        self.assertEqual(token_response.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}")
        profile_response = self.client.get(reverse("current-user"))
        self.assertEqual(profile_response.status_code, 200)
        self.assertEqual(profile_response.data["id"], self.student.pk)

    def test_profile_can_select_a_preset_avatar(self):
        self.client.force_authenticate(self.student)
        response = self.client.patch(
            reverse("current-user"),
            {"first_name": "Student", "avatar_key": User.Avatar.COMET},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["avatar_key"], User.Avatar.COMET)
        self.assertIsNone(response.data["profile_photo_url"])
        self.student.refresh_from_db()
        self.assertEqual(self.student.avatar_key, User.Avatar.COMET)

    def test_profile_photo_upload_keeps_history_and_switches_current_photo(self):
        self.client.force_authenticate(self.student)
        first = self.client.post(
            reverse("profile-photo-list"),
            {"image": self.make_test_image("profile.jpg")},
            format="multipart",
        )
        second = self.client.post(
            reverse("profile-photo-list"),
            {"image": self.make_test_image("avatar-second.webp", "WEBP")},
            format="multipart",
        )
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertTrue(first.data["url"].endswith(".png"))
        self.assertEqual(ProfilePhoto.objects.filter(user=self.student).count(), 2)
        self.assertEqual(ProfilePhoto.objects.filter(user=self.student, is_current=True).count(), 1)

        selected = self.client.post(
            reverse("profile-photo-select", args=[first.data["id"]]),
            {},
            format="json",
        )
        self.assertEqual(selected.status_code, 200)
        self.assertTrue(selected.data["profile_photo_url"])
        first_photo = ProfilePhoto.objects.get(pk=first.data["id"])
        second_photo = ProfilePhoto.objects.get(pk=second.data["id"])
        self.assertTrue(first_photo.is_current)
        self.assertFalse(second_photo.is_current)

    def test_profile_photo_size_limit_and_deleting_current_photo(self):
        self.client.force_authenticate(self.student)
        oversized = self.client.post(
            reverse("profile-photo-list"),
            {
                "image": SimpleUploadedFile(
                    "large.png",
                    b"x" * (5 * 1024 * 1024 + 1),
                    content_type="image/png",
                ),
            },
            format="multipart",
        )
        self.assertEqual(oversized.status_code, 400)

        upload = self.client.post(
            reverse("profile-photo-list"),
            {"image": self.make_test_image()},
            format="multipart",
        )
        deleted = self.client.delete(reverse("profile-photo-detail", args=[upload.data["id"]]))
        self.assertEqual(deleted.status_code, 204)
        self.assertIsNone(self.client.get(reverse("current-user")).data["profile_photo_url"])
        self.assertEqual(ProfilePhoto.objects.filter(user=self.student).count(), 0)

    def test_profile_photo_rejects_non_images_and_is_private_to_owner(self):
        self.client.force_authenticate(self.student)
        invalid = self.client.post(
            reverse("profile-photo-list"),
            {"image": SimpleUploadedFile("not-an-image.png", b"not an image", content_type="image/png")},
            format="multipart",
        )
        self.assertEqual(invalid.status_code, 400)

        upload = self.client.post(
            reverse("profile-photo-list"),
            {"image": self.make_test_image()},
            format="multipart",
        )
        self.assertEqual(upload.status_code, 201)
        self.client.force_authenticate(self.other_student)
        selected = self.client.post(
            reverse("profile-photo-select", args=[upload.data["id"]]),
            {},
            format="json",
        )
        self.assertEqual(selected.status_code, 404)
        self.assertEqual(self.client.get(reverse("profile-photo-list")).data, [])

    def test_parent_children_endpoint_only_returns_linked_students(self):
        self.client.force_authenticate(self.parent)
        response = self.client.get(reverse("parent-children"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["student"]["id"] for item in response.data], [self.student.pk])

    def test_student_can_enroll_and_only_access_enrolled_course_content(self):
        self.client.force_authenticate(self.student)
        enrollment = self.client.post(reverse("enrollment-list"), {"course": self.course.pk}, format="json")
        self.assertEqual(enrollment.status_code, 201)
        self.assertTrue(CourseEnrollment.objects.filter(student=self.student, course=self.course).exists())
        response = self.client.get(reverse("lesson-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.data["results"]], [self.lesson.pk])

    def test_unenrolled_student_cannot_read_course_lessons(self):
        self.client.force_authenticate(self.other_student)
        response = self.client.get(reverse("lesson-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"], [])

    def test_parent_can_read_linked_student_course_content(self):
        CourseEnrollment.objects.create(student=self.student, course=self.course)
        self.client.force_authenticate(self.parent)
        response = self.client.get(reverse("lesson-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.data["results"]], [self.lesson.pk])

    def test_parent_cannot_read_unlinked_child_course_content(self):
        CourseEnrollment.objects.create(student=self.other_student, course=self.course)
        self.client.force_authenticate(self.parent)
        response = self.client.get(reverse("lesson-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"], [])

    def test_teacher_cannot_add_lesson_to_another_teachers_course(self):
        other_teacher = User.objects.create_user(
            username="other-teacher",
            email="other-teacher@example.com",
            password="StrongOtherTeacher!481",
            role=User.Role.TEACHER,
        )
        self.client.force_authenticate(other_teacher)
        response = self.client.post(
            reverse("lesson-list"),
            {"course": self.course.pk, "title": "Unauthorized", "order": 2},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Lesson.objects.filter(title="Unauthorized").exists())

    def test_quiz_api_does_not_expose_answer_key(self):
        CourseEnrollment.objects.create(student=self.student, course=self.course)
        quiz = Quiz.objects.create(course=self.course, title="Algebra check", published=True)
        question = Question.objects.create(
            quiz=quiz,
            prompt="What is 2 + 2?",
            question_type=Question.QuestionType.MULTIPLE_CHOICE,
            options=["3", "4"],
            answer="4",
            order=1,
        )
        self.client.force_authenticate(self.student)
        response = self.client.get(reverse("quiz-detail", args=[quiz.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["questions"][0]["id"], question.pk)
        self.assertNotIn("answer", response.data["questions"][0])
        submission = self.client.post(
            reverse("quiz-submit", args=[quiz.pk]),
            {"answers": {str(question.pk): "4"}},
            format="json",
        )
        self.assertEqual(submission.status_code, 201)
        self.assertEqual(str(submission.data["score"]), "100.00")
        self.assertTrue(
            Grade.objects.filter(
                student=self.student,
                course=self.course,
                source_type=Grade.SourceType.QUIZ,
                source_id=str(submission.data["id"]),
                score=100,
            ).exists()
        )

    def test_assignment_submission_and_teacher_grading_create_student_grade(self):
        CourseEnrollment.objects.create(student=self.student, course=self.course)
        assignment = Assignment.objects.create(
            course=self.course,
            title="Practice",
            due_at=timezone.now() + timedelta(days=1),
            max_score=50,
        )
        self.client.force_authenticate(self.student)
        response = self.client.post(
            reverse("submission-list"),
            {
                "assignment": assignment.pk,
                "submission_text": "My completed work",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)

        self.client.force_authenticate(self.teacher)
        grade_response = self.client.patch(
            reverse("submission-detail", args=[response.data["id"]]),
            {"score": 40, "feedback": "Good work."},
            format="json",
        )
        self.assertEqual(grade_response.status_code, 200)
        grade = Grade.objects.get(
            student=self.student,
            course=self.course,
            source_type=Grade.SourceType.ASSIGNMENT,
            source_id=str(response.data["id"]),
        )
        self.assertEqual(grade.score, 80)
        self.assertEqual(grade.feedback, "Good work.")

    def test_exam_submission_is_scheduled_private_and_creates_grade(self):
        CourseEnrollment.objects.create(student=self.student, course=self.course)
        now = timezone.now()
        exam = Exam.objects.create(
            course=self.course,
            title="Unit examination",
            starts_at=now - timedelta(minutes=1),
            ends_at=now + timedelta(hours=1),
            duration_minutes=30,
            published=True,
        )
        question = ExamQuestion.objects.create(
            exam=exam,
            prompt="What is 5 × 5?",
            options=["10", "25"],
            answer="25",
            points=2,
            order=1,
        )
        self.client.force_authenticate(self.student)
        exam_response = self.client.get(reverse("exam-detail", args=[exam.pk]))
        self.assertEqual(exam_response.status_code, 200)
        self.assertNotIn("answer", exam_response.data["questions"][0])

        start_response = self.client.post(reverse("exam-start", args=[exam.pk]), {}, format="json")
        self.assertEqual(start_response.status_code, 200)
        submit_response = self.client.post(
            reverse("exam-submit", args=[exam.pk]),
            {"answers": {str(question.pk): "25"}},
            format="json",
        )
        self.assertEqual(submit_response.status_code, 200)
        self.assertEqual(str(submit_response.data["score"]), "100.00")
        self.assertTrue(
            Grade.objects.filter(
                student=self.student,
                course=self.course,
                source_type=Grade.SourceType.EXAM,
                source_id=str(start_response.data["id"]),
            ).exists()
        )
        duplicate_response = self.client.post(
            reverse("exam-submit", args=[exam.pk]),
            {"answers": {str(question.pk): "25"}},
            format="json",
        )
        self.assertEqual(duplicate_response.status_code, 400)

    def test_teacher_can_only_create_exam_questions_for_own_course(self):
        other_teacher = User.objects.create_user(
            username="exam-other-teacher",
            email="exam-other-teacher@example.com",
            password="StrongOtherTeacher!481",
            role=User.Role.TEACHER,
        )
        exam = Exam.objects.create(
            course=self.course,
            title="Protected examination",
            starts_at=timezone.now(),
            ends_at=timezone.now() + timedelta(hours=1),
            duration_minutes=30,
        )
        self.client.force_authenticate(other_teacher)
        response = self.client.post(
            reverse("exam-question-list"),
            {"exam": exam.pk, "prompt": "Private question?", "answer": "yes", "order": 1},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(ExamQuestion.objects.filter(exam=exam).exists())

    def test_parent_sees_only_linked_child_grades_and_attendance(self):
        CourseEnrollment.objects.create(student=self.student, course=self.course)
        CourseEnrollment.objects.create(student=self.other_student, course=self.course)
        Grade.objects.create(
            student=self.student,
            course=self.course,
            source_type=Grade.SourceType.MANUAL,
            source_id="parent-visible",
            score=88,
            graded_by=self.teacher,
        )
        Grade.objects.create(
            student=self.other_student,
            course=self.course,
            source_type=Grade.SourceType.MANUAL,
            source_id="private",
            score=42,
            graded_by=self.teacher,
        )
        Attendance.objects.create(
            student=self.student,
            course=self.course,
            date=timezone.localdate(),
            status=Attendance.Status.PRESENT,
            recorded_by=self.teacher,
        )
        Attendance.objects.create(
            student=self.other_student,
            course=self.course,
            date=timezone.localdate(),
            status=Attendance.Status.ABSENT,
            recorded_by=self.teacher,
        )
        self.client.force_authenticate(self.parent)
        grade_response = self.client.get(reverse("grade-list"))
        attendance_response = self.client.get(reverse("attendance-list"))
        self.assertEqual(grade_response.status_code, 200)
        self.assertEqual(attendance_response.status_code, 200)
        self.assertEqual([row["student"] for row in grade_response.data["results"]], [self.student.pk])
        self.assertEqual([row["student"] for row in attendance_response.data["results"]], [self.student.pk])

    def test_parent_calendar_only_includes_events_for_linked_child_courses(self):
        CourseEnrollment.objects.create(student=self.student, course=self.course)
        CourseEnrollment.objects.create(student=self.other_student, course=self.course)
        now = timezone.now()
        event = CalendarEvent.objects.create(
            title="Algebra review",
            event_type=CalendarEvent.EventType.COURSE,
            starts_at=now,
            ends_at=now + timedelta(hours=1),
            course=self.course,
            created_by=self.teacher,
        )
        self.client.force_authenticate(self.parent)
        response = self.client.get(reverse("calendar-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["id"] for row in response.data["results"]], [event.pk])

    def test_student_teacher_messaging_is_scoped_and_notifies_recipient(self):
        CourseEnrollment.objects.create(student=self.student, course=self.course)
        self.client.force_authenticate(self.student)
        contacts = self.client.get(reverse("message-contacts"), {"course": self.course.pk})
        self.assertEqual(contacts.status_code, 200)
        self.assertEqual([item["id"] for item in contacts.data], [self.teacher.pk])

        created = self.client.post(
            reverse("conversation-list"),
            {"course": self.course.pk, "recipient": self.teacher.pk},
            format="json",
        )
        self.assertEqual(created.status_code, 201)
        conversation_id = created.data["id"]
        sent = self.client.post(
            reverse("conversation-messages", args=[conversation_id]),
            {"body": "Could you explain the next lesson?"},
            format="json",
        )
        self.assertEqual(sent.status_code, 201)
        self.assertEqual(
            Message.objects.filter(conversation_id=conversation_id, sender=self.student).count(),
            1,
        )
        self.assertTrue(self.teacher.notifications.filter(kind="message").exists())

        self.client.force_authenticate(self.other_student)
        hidden = self.client.get(reverse("conversation-messages", args=[conversation_id]))
        self.assertEqual(hidden.status_code, 404)

        self.client.force_authenticate(self.teacher)
        inbox = self.client.get(reverse("conversation-messages", args=[conversation_id]))
        self.assertEqual(inbox.status_code, 200)
        message = Message.objects.get(conversation_id=conversation_id)
        message.refresh_from_db()
        self.assertIsNotNone(message.read_at)

    def test_student_cannot_start_conversation_with_unrelated_teacher(self):
        other_teacher = User.objects.create_user(
            username="unrelated-teacher",
            email="unrelated-teacher@example.com",
            password="StrongOtherTeacher!481",
            role=User.Role.TEACHER,
        )
        CourseEnrollment.objects.create(student=self.student, course=self.course)
        self.client.force_authenticate(self.student)
        response = self.client.post(
            reverse("conversation-list"),
            {"course": self.course.pk, "recipient": other_teacher.pk},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Conversation.objects.count(), 0)
