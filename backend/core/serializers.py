from io import BytesIO
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from PIL import Image, UnidentifiedImageError

from .models import (
    Assignment,
    AssignmentSubmission,
    Attendance,
    Book,
    BookCategory,
    CalendarEvent,
    Course,
    CourseEnrollment,
    Conversation,
    Exam,
    ExamAttempt,
    ExamQuestion,
    Grade,
    Lesson,
    LessonProgress,
    Message,
    Notification,
    Question,
    ProfilePhoto,
    Quiz,
    QuizAttempt,
    StudentParent,
    Subject,
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    profile_photo_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "avatar_key",
            "profile_photo_url",
        ]
        read_only_fields = fields

    def get_profile_photo_url(self, obj) -> str | None:
        photo = getattr(obj, "_current_profile_photo", None)
        if photo is None:
            photo = obj.profile_photos.filter(is_current=True).first()
        if not photo:
            return None
        request = self.context.get("request")
        url = photo.image.url
        return request.build_absolute_uri(url) if request else url


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "avatar_key"]


class ProfilePhotoSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = ProfilePhoto
        fields = ["id", "url", "is_current", "uploaded_at"]
        read_only_fields = fields

    def get_url(self, obj) -> str:
        request = self.context.get("request")
        url = obj.image.url
        return request.build_absolute_uri(url) if request else url


class ProfilePhotoUploadSerializer(serializers.ModelSerializer):
    MAX_BYTES = 5 * 1024 * 1024
    MAX_DIMENSION = 4096
    ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}

    class Meta:
        model = ProfilePhoto
        fields = ["image"]

    def validate_image(self, uploaded):
        if uploaded.size > self.MAX_BYTES:
            raise serializers.ValidationError("Choose an image smaller than 5 MB.")
        try:
            uploaded.seek(0)
            with Image.open(BytesIO(uploaded.read())) as image:
                if image.format not in self.ALLOWED_FORMATS:
                    raise serializers.ValidationError("Upload a JPEG, PNG, or WebP image.")
                if image.width > self.MAX_DIMENSION or image.height > self.MAX_DIMENSION:
                    raise serializers.ValidationError("Image dimensions cannot exceed 4096 by 4096 pixels.")
                extension = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}[image.format]
                image.verify()
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as error:
            raise serializers.ValidationError("The uploaded file is not a valid supported image.") from error
        finally:
            uploaded.seek(0)
        uploaded.name = f"profile.{extension}"
        return uploaded

    def create(self, validated_data):
        user = self.context["request"].user
        with transaction.atomic():
            User.objects.select_for_update().get(pk=user.pk)
            ProfilePhoto.objects.filter(user=user, is_current=True).update(is_current=False)
            photo = ProfilePhoto.objects.create(user=user, is_current=True, **validated_data)
        return photo

class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=12, trim_whitespace=False)
    role = serializers.ChoiceField(choices=[("student", "Student"), ("parent", "Parent")])

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "first_name", "last_name", "role"]
        read_only_fields = ["id"]

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        if user.role == User.Role.STUDENT:
            from .models import StudentProfile

            StudentProfile.objects.create(user=user)
        else:
            from .models import ParentProfile

            ParentProfile.objects.create(user=user)
        return user

    def validate_password(self, value):
        validate_password(value)
        return value


class ManagedUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=12, trim_whitespace=False)
    role = serializers.ChoiceField(choices=User.Role.choices)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "is_active",
            "password",
        ]
        read_only_fields = ["id"]

    def validate_password(self, value):
        validate_password(value)
        return value

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        if user.role == User.Role.STUDENT:
            from .models import StudentProfile

            StudentProfile.objects.create(user=user)
        elif user.role == User.Role.PARENT:
            from .models import ParentProfile

            ParentProfile.objects.create(user=user)
        elif user.role == User.Role.TEACHER:
            from .models import TeacherProfile

            TeacherProfile.objects.create(user=user)
        return user


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["id", "name", "slug", "description"]


class CourseSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    teacher_name = serializers.SerializerMethodField()
    enrollment_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "subject",
            "subject_name",
            "teacher",
            "teacher_name",
            "academic_level",
            "thumbnail_url",
            "status",
            "enrollment_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "teacher", "status", "created_at", "updated_at", "enrollment_count"]

    def get_teacher_name(self, obj) -> str:
        return obj.teacher.get_full_name() or obj.teacher.username


class EnrollmentSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source="course.title", read_only=True)
    student = UserSerializer(read_only=True)

    class Meta:
        model = CourseEnrollment
        fields = ["id", "course", "course_title", "student", "status", "enrolled_at"]
        read_only_fields = ["id", "status", "enrolled_at"]


class LessonProgressUpdateSerializer(serializers.Serializer):
    lesson = serializers.PrimaryKeyRelatedField(queryset=Lesson.objects.select_related("course").all())
    completed = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        user = self.context["request"].user
        lesson = attrs["lesson"]
        if user.role != User.Role.STUDENT or not CourseEnrollment.objects.filter(
            student=user,
            course=lesson.course,
            status=CourseEnrollment.Status.ACTIVE,
        ).exists():
            raise serializers.ValidationError("You must be an active student in this course.")
        return attrs


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ["id", "course", "title", "content", "video_url", "order", "duration_minutes", "created_at"]
        read_only_fields = ["id", "created_at"]


class LessonProgressSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source="lesson.title", read_only=True)

    class Meta:
        model = LessonProgress
        fields = ["id", "lesson", "lesson_title", "completed_at", "updated_at"]
        read_only_fields = ["id", "lesson_title", "updated_at"]


class BookCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BookCategory
        fields = ["id", "name", "slug"]


class BookSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "author",
            "description",
            "cover_url",
            "resource_url",
            "subject",
            "subject_name",
            "category",
            "category_name",
            "academic_level",
            "published_on",
        ]


class AssignmentSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source="course.title", read_only=True)

    class Meta:
        model = Assignment
        fields = ["id", "course", "course_title", "title", "description", "due_at", "max_score", "created_at"]
        read_only_fields = ["id", "created_at"]


class AssignmentSubmissionSerializer(serializers.ModelSerializer):
    student = UserSerializer(read_only=True)

    class Meta:
        model = AssignmentSubmission
        fields = [
            "id",
            "assignment",
            "student",
            "submission_text",
            "resource_url",
            "status",
            "score",
            "feedback",
            "submitted_at",
            "graded_at",
        ]
        read_only_fields = ["id", "student", "status", "score", "feedback", "submitted_at", "graded_at"]

    def create(self, validated_data):
        assignment = validated_data.pop("assignment")
        return AssignmentSubmission.objects.update_or_create(
            assignment=assignment,
            student=self.context["request"].user,
            defaults={
                **validated_data,
                "status": AssignmentSubmission.Status.SUBMITTED,
                "score": None,
                "feedback": "",
                "graded_at": None,
                "submitted_at": timezone.now(),
            },
        )[0]


class AssignmentGradeSerializer(serializers.ModelSerializer):
    score = serializers.IntegerField(min_value=0, max_value=100)

    class Meta:
        model = AssignmentSubmission
        fields = ["score", "feedback"]

    def validate_score(self, value):
        if value > self.instance.assignment.max_score:
            raise serializers.ValidationError("The score cannot exceed the assignment maximum.")
        return value


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ["id", "prompt", "question_type", "options", "points", "order"]


class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ["id", "course", "title", "duration_minutes", "questions"]


class QuizAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAttempt
        fields = ["id", "quiz", "answers", "score", "started_at", "submitted_at"]
        read_only_fields = ["id", "quiz", "score", "started_at", "submitted_at"]


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "title", "message", "kind", "read_at", "created_at"]
        read_only_fields = ["id", "title", "message", "kind", "created_at"]


class StudentParentSerializer(serializers.ModelSerializer):
    student = UserSerializer(read_only=True)

    class Meta:
        model = StudentParent
        fields = ["id", "student", "relationship", "created_at"]


class QuizSubmissionSerializer(serializers.Serializer):
    answers = serializers.DictField(child=serializers.JSONField())

    def validate(self, attrs):
        quiz = self.context["quiz"]
        user = self.context["request"].user
        question_ids = {str(question_id) for question_id in quiz.questions.values_list("id", flat=True)}
        if set(attrs["answers"]) - question_ids:
            raise serializers.ValidationError({"answers": "Answers may only reference questions in this quiz."})
        enrollment_exists = CourseEnrollment.objects.filter(student=user, course=quiz.course).exists()
        if user.role != User.Role.STUDENT or not enrollment_exists:
            raise serializers.ValidationError("You must be enrolled in this course to submit the quiz.")
        if not quiz.published:
            raise serializers.ValidationError("This quiz is not available.")
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        quiz = self.context["quiz"]
        user = self.context["request"].user
        questions = list(quiz.questions.all())
        correct = sum(
            question.points
            for question in questions
            if validated_data["answers"].get(str(question.pk)) == question.answer
        )
        total = sum(question.points for question in questions)
        score = round((correct / total) * 100, 2) if total else 0
        return QuizAttempt.objects.create(
            quiz=quiz,
            student=user,
            answers=validated_data["answers"],
            score=score,
            submitted_at=timezone.now(),
        )


class ExamQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamQuestion
        fields = ["id", "prompt", "options", "points", "order"]


class ExamQuestionManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamQuestion
        fields = ["id", "exam", "prompt", "options", "answer", "points", "order"]
        read_only_fields = ["id"]


class ExamSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source="course.title", read_only=True)
    questions = ExamQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Exam
        fields = [
            "id",
            "course",
            "course_title",
            "title",
            "instructions",
            "starts_at",
            "ends_at",
            "duration_minutes",
            "published",
            "questions",
        ]
        read_only_fields = ["id", "course_title", "questions"]

    def validate(self, attrs):
        start = attrs.get("starts_at", getattr(self.instance, "starts_at", None))
        end = attrs.get("ends_at", getattr(self.instance, "ends_at", None))
        if start and end and end <= start:
            raise serializers.ValidationError({"ends_at": "The exam must end after it starts."})
        return attrs


class ExamAttemptSerializer(serializers.ModelSerializer):
    exam_title = serializers.CharField(source="exam.title", read_only=True)

    class Meta:
        model = ExamAttempt
        fields = ["id", "exam", "exam_title", "answers", "score", "started_at", "submitted_at"]
        read_only_fields = fields


class ExamSubmissionSerializer(serializers.Serializer):
    answers = serializers.DictField(child=serializers.JSONField())

    def validate(self, attrs):
        exam = self.context["exam"]
        student = self.context["request"].user
        now = timezone.now()
        if student.role != User.Role.STUDENT or not CourseEnrollment.objects.filter(
            student=student,
            course=exam.course,
            status=CourseEnrollment.Status.ACTIVE,
        ).exists():
            raise serializers.ValidationError("You must be an active student in this course.")
        if not exam.published or now < exam.starts_at or now > exam.ends_at:
            raise serializers.ValidationError("This examination is not currently open.")
        attempt = exam.attempts.filter(student=student, submitted_at__isnull=True).first()
        if not attempt:
            raise serializers.ValidationError("Start the examination before submitting your answers.")
        if now > attempt.started_at + timedelta(minutes=exam.duration_minutes):
            raise serializers.ValidationError("The examination time limit has expired.")
        question_ids = {str(question_id) for question_id in exam.questions.values_list("id", flat=True)}
        if set(attrs["answers"]) != question_ids:
            raise serializers.ValidationError({"answers": "Provide one answer for every question in the examination."})
        attrs["attempt"] = attempt
        return attrs


class GradeSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    course_title = serializers.CharField(source="course.title", read_only=True)

    class Meta:
        model = Grade
        fields = [
            "id",
            "student",
            "student_name",
            "course",
            "course_title",
            "source_type",
            "source_id",
            "score",
            "feedback",
            "graded_by",
            "graded_at",
        ]
        read_only_fields = ["id", "student_name", "graded_by", "graded_at"]

    def get_student_name(self, obj) -> str:
        return obj.student.get_full_name() or obj.student.username

    def validate(self, attrs):
        if attrs.get("source_type") == Grade.SourceType.MANUAL and not attrs.get("source_id"):
            attrs["source_id"] = f"manual-{timezone.now().timestamp()}"
        return attrs


class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    course_title = serializers.CharField(source="course.title", read_only=True)
    recorded_by = UserSerializer(read_only=True)

    class Meta:
        model = Attendance
        fields = [
            "id",
            "course",
            "course_title",
            "student",
            "student_name",
            "date",
            "status",
            "note",
            "recorded_by",
            "created_at",
        ]
        read_only_fields = ["id", "course_title", "student_name", "recorded_by", "created_at"]

    def get_student_name(self, obj) -> str:
        return obj.student.get_full_name() or obj.student.username

    def validate(self, attrs):
        course = attrs.get("course", self.instance.course if self.instance else None)
        student = attrs.get("student", self.instance.student if self.instance else None)
        if course and student and not CourseEnrollment.objects.filter(
            course=course,
            student=student,
        ).exists():
            raise serializers.ValidationError({"student": "The student is not enrolled in this course."})
        return attrs


class CalendarEventSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source="course.title", read_only=True)

    class Meta:
        model = CalendarEvent
        fields = [
            "id",
            "title",
            "description",
            "event_type",
            "starts_at",
            "ends_at",
            "course",
            "course_title",
            "created_by",
            "created_at",
        ]
        read_only_fields = ["id", "course_title", "created_by", "created_at"]

    def validate(self, attrs):
        start = attrs.get("starts_at", getattr(self.instance, "starts_at", None))
        end = attrs.get("ends_at", getattr(self.instance, "ends_at", None))
        if start and end and end < start:
            raise serializers.ValidationError({"ends_at": "The event must end after it starts."})
        return attrs


class MessageParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "role"]
        read_only_fields = fields


class ConversationSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source="course.title", read_only=True)
    participants = MessageParticipantSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ["id", "course", "course_title", "title", "participants", "created_at", "updated_at"]
        read_only_fields = fields


class ConversationCreateSerializer(serializers.Serializer):
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all())
    recipient = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(is_active=True))
    title = serializers.CharField(max_length=200, required=False, allow_blank=True)

    def validate(self, attrs):
        user = self.context["request"].user
        course = attrs["course"]
        recipient = attrs["recipient"]
        if recipient.pk == user.pk:
            raise serializers.ValidationError({"recipient": "You cannot start a conversation with yourself."})

        allowed = user.is_superuser or user.role == User.Role.ADMIN
        if user.role == User.Role.TEACHER and course.teacher_id == user.pk:
            if recipient.role == User.Role.STUDENT:
                allowed = CourseEnrollment.objects.filter(
                    student=recipient,
                    course=course,
                    status=CourseEnrollment.Status.ACTIVE,
                ).exists()
            elif recipient.role == User.Role.PARENT:
                allowed = StudentParent.objects.filter(
                    parent=recipient,
                    student__course_enrollments__course=course,
                    student__course_enrollments__status=CourseEnrollment.Status.ACTIVE,
                ).exists()
        elif user.role == User.Role.STUDENT and recipient.pk == course.teacher_id:
            allowed = CourseEnrollment.objects.filter(
                student=user,
                course=course,
                status=CourseEnrollment.Status.ACTIVE,
            ).exists()
        elif user.role == User.Role.PARENT and recipient.pk == course.teacher_id:
            allowed = StudentParent.objects.filter(
                parent=user,
                student__course_enrollments__course=course,
                student__course_enrollments__status=CourseEnrollment.Status.ACTIVE,
            ).exists()

        if not allowed:
            raise serializers.ValidationError(
                {"recipient": "You can only message people connected to your course or linked students."}
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        request = self.context["request"]
        conversation = Conversation.objects.create(
            course=validated_data["course"],
            title=validated_data.get("title") or validated_data["course"].title,
            created_by=request.user,
        )
        conversation.participants.add(request.user, validated_data["recipient"])
        return conversation


class MessageSerializer(serializers.ModelSerializer):
    sender = MessageParticipantSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ["id", "sender", "body", "read_at", "sent_at"]
        read_only_fields = fields


class MessageCreateSerializer(serializers.Serializer):
    body = serializers.CharField(max_length=5000, trim_whitespace=True)
