import uuid

from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone


def profile_photo_path(instance, filename):
    extension = filename.rsplit(".", 1)[-1].lower()
    return f"profile-photos/{instance.user_id}/{uuid.uuid4().hex}.{extension}"


class EDUCOREUserManager(DjangoUserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role", "admin")
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    class Avatar(models.TextChoices):
        AURORA = "aurora", "Aurora"
        ATLAS = "atlas", "Atlas"
        NOVA = "nova", "Nova"
        RIVER = "river", "River"
        SAGE = "sage", "Sage"
        COMET = "comet", "Comet"
        MAPLE = "maple", "Maple"
        ORBIT = "orbit", "Orbit"

    class Role(models.TextChoices):
        STUDENT = "student", "Student"
        PARENT = "parent", "Parent"
        TEACHER = "teacher", "Teacher"
        ADMIN = "admin", "Administrator"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.STUDENT, db_index=True)
    avatar_key = models.CharField(max_length=16, choices=Avatar.choices, default=Avatar.AURORA)
    objects = EDUCOREUserManager()

    def __str__(self):
        return self.get_full_name() or self.username


class ProfilePhoto(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="profile_photos")
    image = models.ImageField(upload_to=profile_photo_path)
    is_current = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(is_current=True),
                name="unique_current_profile_photo",
            ),
        ]
        indexes = [models.Index(fields=["user", "uploaded_at"])]


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")
    academic_level = models.CharField(max_length=80, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Student profile: {self.user}"


class ParentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="parent_profile")


class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="teacher_profile")
    biography = models.TextField(blank=True)
    specialization = models.CharField(max_length=120, blank=True)


class StudentParent(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="parent_links")
    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name="child_links")
    relationship = models.CharField(max_length=40, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["student", "parent"], name="unique_student_parent_link"),
            models.CheckConstraint(condition=~Q(student=models.F("parent")), name="parent_cannot_be_student"),
        ]
        indexes = [models.Index(fields=["parent", "student"])]

    def __str__(self):
        return f"{self.parent} -> {self.student}"


class Subject(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Course(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField(blank=True)
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name="courses")
    teacher = models.ForeignKey(User, on_delete=models.PROTECT, related_name="courses_taught")
    academic_level = models.CharField(max_length=80, blank=True)
    thumbnail_url = models.URLField(blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]
        indexes = [models.Index(fields=["status", "subject", "academic_level"])]

    def __str__(self):
        return self.title


class CourseEnrollment(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        PAUSED = "paused", "Paused"

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="course_enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["student", "course"], name="unique_course_enrollment"),
        ]
        indexes = [models.Index(fields=["student", "status"])]


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    video_url = models.URLField(blank=True)
    order = models.PositiveIntegerField(default=1)
    duration_minutes = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["course", "order"]
        constraints = [models.UniqueConstraint(fields=["course", "order"], name="unique_lesson_order")]


class LessonProgress(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="lesson_progress")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="progress_records")
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["student", "lesson"], name="unique_student_lesson_progress"),
        ]


class BookCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "book categories"

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    cover_url = models.URLField(blank=True)
    resource_url = models.URLField(blank=True)
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name="books")
    category = models.ForeignKey(BookCategory, on_delete=models.PROTECT, related_name="books")
    academic_level = models.CharField(max_length=80, blank=True)
    published_on = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]
        indexes = [models.Index(fields=["subject", "academic_level"])]

    def __str__(self):
        return self.title


class Bookmark(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookmarks")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="bookmarks")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["student", "book"], name="unique_student_bookmark")]


class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="assignments")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_at = models.DateTimeField(db_index=True)
    max_score = models.PositiveSmallIntegerField(
        default=100,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["due_at"]
        indexes = [models.Index(fields=["course", "due_at"])]
        constraints = [
            models.CheckConstraint(condition=Q(max_score__gte=1, max_score__lte=100), name="assignment_max_score_in_range"),
        ]


class AssignmentSubmission(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        GRADED = "graded", "Graded"
        RETURNED = "returned", "Returned"

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="assignment_submissions")
    submission_text = models.TextField(blank=True)
    resource_url = models.URLField(blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.SUBMITTED)
    score = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MaxValueValidator(100)])
    feedback = models.TextField(blank=True)
    submitted_at = models.DateTimeField(default=timezone.now)
    graded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["assignment", "student"], name="unique_assignment_submission"),
            models.CheckConstraint(
                condition=Q(score__isnull=True) | Q(score__gte=0, score__lte=100),
                name="assignment_score_in_range",
            ),
        ]
        indexes = [models.Index(fields=["student", "status"])]


class Quiz(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="quizzes")
    title = models.CharField(max_length=200)
    duration_minutes = models.PositiveSmallIntegerField(default=15)
    published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]


class Question(models.Model):
    class QuestionType(models.TextChoices):
        MULTIPLE_CHOICE = "multiple_choice", "Multiple choice"
        TRUE_FALSE = "true_false", "True or false"
        SHORT_ANSWER = "short_answer", "Short answer"

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    prompt = models.TextField()
    question_type = models.CharField(max_length=20, choices=QuestionType.choices)
    options = models.JSONField(default=list, blank=True)
    answer = models.JSONField()
    explanation = models.TextField(blank=True)
    points = models.PositiveSmallIntegerField(default=1)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order"]
        constraints = [models.UniqueConstraint(fields=["quiz", "order"], name="unique_quiz_question_order")]


class QuizAttempt(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="quiz_attempts")
    answers = models.JSONField(default=dict)
    score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["student", "quiz", "started_at"])]


class Exam(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="exams")
    title = models.CharField(max_length=200)
    instructions = models.TextField(blank=True)
    starts_at = models.DateTimeField(db_index=True)
    ends_at = models.DateTimeField(db_index=True)
    duration_minutes = models.PositiveSmallIntegerField()
    published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["starts_at"]
        indexes = [models.Index(fields=["course", "starts_at", "ends_at"])]
        constraints = [
            models.CheckConstraint(condition=Q(ends_at__gt=models.F("starts_at")), name="exam_end_after_start"),
        ]

    def __str__(self):
        return self.title


class ExamQuestion(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="questions")
    prompt = models.TextField()
    options = models.JSONField(default=list, blank=True)
    answer = models.JSONField()
    points = models.PositiveSmallIntegerField(default=1)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order"]
        constraints = [models.UniqueConstraint(fields=["exam", "order"], name="unique_exam_question_order")]


class ExamAttempt(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="attempts")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="exam_attempts")
    answers = models.JSONField(default=dict)
    score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["exam", "student"], name="unique_exam_student_attempt"),
        ]
        indexes = [models.Index(fields=["student", "exam", "started_at"])]


class Grade(models.Model):
    class SourceType(models.TextChoices):
        ASSIGNMENT = "assignment", "Assignment"
        QUIZ = "quiz", "Quiz"
        EXAM = "exam", "Examination"
        MANUAL = "manual", "Manual"

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="grades")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="grades")
    source_type = models.CharField(max_length=16, choices=SourceType.choices)
    source_id = models.CharField(max_length=64, blank=True)
    score = models.DecimalField(max_digits=7, decimal_places=2, validators=[MaxValueValidator(100)])
    feedback = models.TextField(blank=True)
    graded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="grades_given")
    graded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-graded_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "course", "source_type", "source_id"],
                name="unique_student_course_grade_source",
            ),
            models.CheckConstraint(condition=Q(score__gte=0, score__lte=100), name="grade_score_in_range"),
        ]
        indexes = [models.Index(fields=["student", "course", "graded_at"])]


class Attendance(models.Model):
    class Status(models.TextChoices):
        PRESENT = "present", "Present"
        ABSENT = "absent", "Absent"
        LATE = "late", "Late"
        EXCUSED = "excused", "Excused"

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="attendance_records")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="attendance_records")
    date = models.DateField(db_index=True)
    status = models.CharField(max_length=12, choices=Status.choices)
    note = models.CharField(max_length=240, blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="attendance_recorded")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "student__last_name"]
        constraints = [
            models.UniqueConstraint(fields=["course", "student", "date"], name="unique_course_student_attendance_date"),
        ]
        indexes = [models.Index(fields=["student", "date", "status"])]


class CalendarEvent(models.Model):
    class EventType(models.TextChoices):
        COURSE = "course", "Course"
        EXAM = "exam", "Examination"
        ASSIGNMENT = "assignment", "Assignment"
        SCHOOL = "school", "School event"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    event_type = models.CharField(max_length=16, choices=EventType.choices)
    starts_at = models.DateTimeField(db_index=True)
    ends_at = models.DateTimeField()
    course = models.ForeignKey(Course, null=True, blank=True, on_delete=models.CASCADE, related_name="calendar_events")
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="calendar_events")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["starts_at"]
        constraints = [
            models.CheckConstraint(condition=Q(ends_at__gte=models.F("starts_at")), name="calendar_event_end_after_start"),
        ]
        indexes = [models.Index(fields=["course", "starts_at"])]


class Conversation(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="conversations")
    title = models.CharField(max_length=200, blank=True)
    participants = models.ManyToManyField(User, related_name="conversations")
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="conversations_created")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [models.Index(fields=["course", "updated_at"])]


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.PROTECT, related_name="messages_sent")
    body = models.TextField(max_length=5000)
    read_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sent_at"]
        indexes = [
            models.Index(fields=["conversation", "sent_at"]),
            models.Index(fields=["conversation", "read_at"]),
        ]


class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=180)
    message = models.TextField()
    kind = models.CharField(max_length=40, default="general")
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["recipient", "read_at", "created_at"])]


class AuditLog(models.Model):
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="audit_events")
    action = models.CharField(max_length=100)
    object_type = models.CharField(max_length=100)
    object_id = models.CharField(max_length=64, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["object_type", "object_id", "created_at"])]
