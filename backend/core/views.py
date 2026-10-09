import logging
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.conf import settings
from django.db import DatabaseError, connection
from django.db.models import Count, Q
from django.db import transaction
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import (
    Assignment,
    AssignmentSubmission,
    Attendance,
    Book,
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
    ProfilePhoto,
    Quiz,
    StudentParent,
    Subject,
    User,
)
from .permissions import CourseContentPermission, CoursePermission, EDUCOREAdminPermission, ParentPermission
from .serializers import (
    AssignmentSerializer,
    AssignmentGradeSerializer,
    AssignmentSubmissionSerializer,
    AttendanceSerializer,
    BookSerializer,
    CalendarEventSerializer,
    CourseSerializer,
    ConversationCreateSerializer,
    ConversationSerializer,
    EnrollmentSerializer,
    ExamAttemptSerializer,
    ExamQuestionManagementSerializer,
    ExamSerializer,
    ExamSubmissionSerializer,
    GradeSerializer,
    LessonProgressSerializer,
    LessonProgressUpdateSerializer,
    LessonSerializer,
    ManagedUserSerializer,
    NotificationSerializer,
    MessageCreateSerializer,
    MessageParticipantSerializer,
    MessageSerializer,
    ProfilePhotoSerializer,
    ProfilePhotoUploadSerializer,
    ProfileUpdateSerializer,
    QuizAttemptSerializer,
    QuizSerializer,
    QuizSubmissionSerializer,
    RegistrationSerializer,
    StudentParentSerializer,
    SubjectSerializer,
    UserSerializer,
)

class LoginThrottle(AnonRateThrottle):
    scope = "auth"


class MessagingThrottle(UserRateThrottle):
    scope = "messaging"


class EDUCORETokenObtainPairView(TokenObtainPairView):
    throttle_classes = [LoginThrottle]


logger = logging.getLogger(__name__)


@extend_schema(summary="Health check", responses={200: dict})
@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    try:
        connection.ensure_connection()
    except DatabaseError:
        logger.exception("EDUCORE health check could not connect to the database.")
        return Response(
            {"status": "error", "service": "EDUCORE", "database": "unavailable"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    return Response({
        "status": "ok",
        "service": "EDUCORE",
        "database": "available",
        "environment": "development" if settings.DEBUG else "production",
    })


class RegistrationView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]

    @extend_schema(request=RegistrationSerializer, responses={201: UserSerializer})
    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            UserSerializer(user, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=UserSerializer)
    def get(self, request):
        request.user._current_profile_photo = request.user.profile_photos.filter(is_current=True).first()
        return Response(UserSerializer(request.user, context={"request": request}).data)

    @extend_schema(request=ProfileUpdateSerializer, responses=UserSerializer)
    def patch(self, request):
        serializer = ProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        request.user._current_profile_photo = request.user.profile_photos.filter(is_current=True).first()
        return Response(UserSerializer(request.user, context={"request": request}).data)


class ProfilePhotoViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    throttle_classes = [UserRateThrottle]
    queryset = ProfilePhoto.objects.none()

    def get_queryset(self):
        return ProfilePhoto.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return ProfilePhotoUploadSerializer
        return ProfilePhotoSerializer

    def list(self, request):
        photos = self.get_queryset()
        return Response(ProfilePhotoSerializer(photos, many=True, context={"request": request}).data)

    @extend_schema(
        request=ProfilePhotoUploadSerializer,
        responses={201: ProfilePhotoSerializer},
    )
    def create(self, request):
        serializer = ProfilePhotoUploadSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        photo = serializer.save()
        return Response(
            ProfilePhotoSerializer(photo, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="select")
    def select(self, request, pk=None):
        with transaction.atomic():
            User.objects.select_for_update().get(pk=request.user.pk)
            photo = self.get_queryset().select_for_update().filter(pk=pk).first()
            if photo is None:
                raise NotFound()
            self.get_queryset().exclude(pk=photo.pk).update(is_current=False)
            if not photo.is_current:
                photo.is_current = True
                photo.save(update_fields=["is_current"])
        request.user._current_profile_photo = photo
        return Response(UserSerializer(request.user, context={"request": request}).data)

    def destroy(self, request, pk=None):
        photo = self.get_object()
        was_current = photo.is_current
        image = photo.image
        photo.delete()
        if image:
            transaction.on_commit(lambda: image.delete(save=False))
        if was_current:
            request.user._current_profile_photo = None
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminUserViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    permission_classes = [EDUCOREAdminPermission]
    serializer_class = ManagedUserSerializer
    queryset = User.objects.all().order_by("username")
    filter_backends = [filters.SearchFilter]
    search_fields = ["username", "email", "first_name", "last_name"]


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        user = request.user
        if user.role == User.Role.STUDENT:
            enrollments = CourseEnrollment.objects.filter(student=user).select_related("course")
            return Response({
                "role": user.role,
                "course_count": enrollments.count(),
                "active_courses": enrollments.filter(status=CourseEnrollment.Status.ACTIVE).count(),
                "completed_courses": enrollments.filter(status=CourseEnrollment.Status.COMPLETED).count(),
                "completed_lessons": LessonProgress.objects.filter(student=user, completed_at__isnull=False).count(),
                "pending_assignments": Assignment.objects.filter(
                    course__enrollments__student=user,
                    due_at__gte=timezone.now(),
                ).exclude(submissions__student=user).distinct().count(),
                "upcoming_assignments": AssignmentSerializer(
                    Assignment.objects.filter(
                        course__enrollments__student=user,
                        due_at__gte=timezone.now(),
                    ).order_by("due_at")[:5],
                    many=True,
                ).data,
                "courses": CourseSerializer(
                    Course.objects.filter(enrollments__student=user)
                    .select_related("subject", "teacher")
                    .annotate(enrollment_count=Count("enrollments", distinct=True))
                    .distinct(),
                    many=True,
                ).data,
            })
        if user.role == User.Role.PARENT:
            child_ids = StudentParent.objects.filter(parent=user).values_list("student_id", flat=True)
            return Response({
                "role": user.role,
                "children": UserSerializer(
                    User.objects.filter(id__in=child_ids),
                    many=True,
                    context={"request": self.request},
                ).data,
                "child_count": StudentParent.objects.filter(parent=user).count(),
                "unread_notifications": user.notifications.filter(read_at__isnull=True).count(),
            })
        if user.role == User.Role.TEACHER:
            courses = Course.objects.filter(teacher=user).annotate(enrollment_count=Count("enrollments", distinct=True))
            return Response({
                "role": user.role,
                "course_count": courses.count(),
                "learner_count": CourseEnrollment.objects.filter(course__teacher=user).values("student").distinct().count(),
                "courses": CourseSerializer(courses.select_related("subject", "teacher"), many=True).data,
            })
        return Response({
            "role": user.role,
            "user_count": User.objects.count(),
            "student_count": User.objects.filter(role=User.Role.STUDENT, is_active=True).count(),
            "teacher_count": User.objects.filter(role=User.Role.TEACHER, is_active=True).count(),
            "course_count": Course.objects.count(),
        })


class SubjectViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [AllowAny]


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.none()
    serializer_class = CourseSerializer
    permission_classes = [CoursePermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "description", "subject__name", "teacher__first_name", "teacher__last_name"]
    ordering_fields = ["title", "created_at"]
    ordering = ["title"]

    def get_queryset(self):
        user = self.request.user
        queryset = Course.objects.select_related("subject", "teacher").annotate(
            enrollment_count=Count("enrollments", distinct=True)
        )
        if not user.is_authenticated:
            return queryset.filter(status=Course.Status.PUBLISHED)
        if user.is_superuser or user.role == User.Role.ADMIN:
            return queryset
        visible = Q(status=Course.Status.PUBLISHED)
        if user.role == User.Role.TEACHER:
            visible |= Q(teacher=user)
        elif user.role == User.Role.STUDENT:
            visible |= Q(enrollments__student=user)
        elif user.role == User.Role.PARENT:
            visible |= Q(enrollments__student__parent_links__parent=user)
        return queryset.filter(visible).distinct()

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user)


class EnrollmentViewSet(viewsets.ModelViewSet):
    queryset = CourseEnrollment.objects.none()
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        queryset = CourseEnrollment.objects.select_related("course", "student")
        if user.is_superuser or user.role == User.Role.ADMIN:
            return queryset
        if user.role == User.Role.STUDENT:
            return queryset.filter(student=user)
        if user.role == User.Role.PARENT:
            return queryset.filter(student__parent_links__parent=user)
        if user.role == User.Role.TEACHER:
            return queryset.filter(course__teacher=user)
        return queryset.none()

    def create(self, request, *args, **kwargs):
        if request.user.role != User.Role.STUDENT:
            raise PermissionDenied("Only students can enroll in a course.")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        course = serializer.validated_data["course"]
        if course.status != Course.Status.PUBLISHED:
            raise PermissionDenied("This course is not open for enrollment.")
        enrollment, created = CourseEnrollment.objects.get_or_create(student=request.user, course=course)
        return Response(
            self.get_serializer(enrollment).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.none()
    serializer_class = LessonSerializer
    permission_classes = [CourseContentPermission]
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        queryset = Lesson.objects.select_related("course", "course__teacher")
        if not user.is_authenticated:
            return queryset.none()
        if user.is_superuser or user.role == User.Role.ADMIN:
            return queryset
        if user.role == User.Role.TEACHER:
            return queryset.filter(course__teacher=user)
        if user.role == User.Role.STUDENT:
            return queryset.filter(course__enrollments__student=user, course__enrollments__status=CourseEnrollment.Status.ACTIVE)
        if user.role == User.Role.PARENT:
            return queryset.filter(course__enrollments__student__parent_links__parent=user).distinct()
        return queryset.none()

    def perform_create(self, serializer):
        user = self.request.user
        course = serializer.validated_data["course"]
        if not user.is_superuser and user.role != User.Role.ADMIN and (
            user.role != User.Role.TEACHER or course.teacher_id != user.pk
        ):
            raise PermissionDenied("You can only add lessons to your own courses.")
        serializer.save()

    def perform_update(self, serializer):
        user = self.request.user
        course = serializer.validated_data.get("course", serializer.instance.course)
        if not user.is_superuser and user.role != User.Role.ADMIN and (
            user.role != User.Role.TEACHER or course.teacher_id != user.pk
        ):
            raise PermissionDenied("You can only update lessons in your own courses.")
        serializer.save()


class LessonProgressViewSet(viewsets.ModelViewSet):
    queryset = LessonProgress.objects.none()
    serializer_class = LessonProgressSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.STUDENT:
            return LessonProgress.objects.filter(student=user).select_related("lesson")
        if user.role == User.Role.PARENT:
            return LessonProgress.objects.filter(student__parent_links__parent=user).select_related("lesson", "student").distinct()
        if user.role == User.Role.ADMIN or user.is_superuser:
            return LessonProgress.objects.select_related("lesson", "student")
        return LessonProgress.objects.filter(lesson__course__teacher=user).select_related("lesson", "student")

    def create(self, request, *args, **kwargs):
        if request.user.role != User.Role.STUDENT:
            raise PermissionDenied("Only students can update their lesson progress.")
        serializer = LessonProgressUpdateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        lesson = serializer.validated_data["lesson"]
        progress, _ = LessonProgress.objects.get_or_create(student=request.user, lesson=lesson)
        if serializer.validated_data["completed"]:
            progress.completed_at = timezone.now()
            progress.save(update_fields=["completed_at", "updated_at"])
        return Response(self.get_serializer(progress).data, status=status.HTTP_200_OK)


class BookViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Book.objects.select_related("subject", "category")
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "author", "description", "subject__name", "category__name"]
    ordering_fields = ["title", "published_on"]


class AssignmentViewSet(viewsets.ModelViewSet):
    queryset = Assignment.objects.none()
    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        queryset = Assignment.objects.select_related("course", "course__teacher")
        if user.is_superuser or user.role == User.Role.ADMIN:
            return queryset
        if user.role == User.Role.TEACHER:
            return queryset.filter(course__teacher=user)
        if user.role == User.Role.STUDENT:
            return queryset.filter(course__enrollments__student=user).distinct()
        if user.role == User.Role.PARENT:
            return queryset.filter(course__enrollments__student__parent_links__parent=user).distinct()
        return queryset.none()

    def perform_create(self, serializer):
        user = self.request.user
        course = serializer.validated_data["course"]
        if not user.is_superuser and user.role != User.Role.ADMIN and (
            user.role != User.Role.TEACHER or course.teacher_id != user.pk
        ):
            raise PermissionDenied("You can only create assignments for your own courses.")
        serializer.save()

    def perform_update(self, serializer):
        user = self.request.user
        assignment = self.get_object()
        course = serializer.validated_data.get("course", assignment.course)
        if not user.is_superuser and user.role != User.Role.ADMIN and (
            user.role != User.Role.TEACHER or assignment.course.teacher_id != user.pk or course.teacher_id != user.pk
        ):
            raise PermissionDenied("You can only update assignments for your own courses.")
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        if not user.is_superuser and user.role != User.Role.ADMIN and (
            user.role != User.Role.TEACHER or instance.course.teacher_id != user.pk
        ):
            raise PermissionDenied("You can only delete assignments for your own courses.")
        instance.delete()


class AssignmentSubmissionViewSet(viewsets.ModelViewSet):
    queryset = AssignmentSubmission.objects.none()
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return AssignmentGradeSerializer
        return AssignmentSubmissionSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = AssignmentSubmission.objects.select_related("assignment", "assignment__course", "student")
        if user.is_superuser or user.role == User.Role.ADMIN:
            return queryset
        if user.role == User.Role.STUDENT:
            return queryset.filter(student=user)
        if user.role == User.Role.PARENT:
            return queryset.filter(student__parent_links__parent=user).distinct()
        if user.role == User.Role.TEACHER:
            return queryset.filter(assignment__course__teacher=user)
        return queryset.none()

    def perform_update(self, serializer):
        user = self.request.user
        submission = self.get_object()
        if not user.is_superuser and user.role != User.Role.ADMIN and (
            user.role != User.Role.TEACHER or submission.assignment.course.teacher_id != user.pk
        ):
            raise PermissionDenied("Only the assigned teacher can grade this submission.")
        with transaction.atomic():
            submission = serializer.save(status=AssignmentSubmission.Status.GRADED, graded_at=timezone.now())
            Grade.objects.update_or_create(
                student=submission.student,
                course=submission.assignment.course,
                source_type=Grade.SourceType.ASSIGNMENT,
                source_id=str(submission.pk),
                defaults={
                    "score": (
                        Decimal(submission.score) * Decimal("100") / Decimal(submission.assignment.max_score)
                    ).quantize(Decimal("0.01")),
                    "graded_by": user,
                    "feedback": submission.feedback,
                },
            )

    def create(self, request, *args, **kwargs):
        if request.user.role != User.Role.STUDENT:
            raise PermissionDenied("Only students can submit assignments.")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        assignment = serializer.validated_data["assignment"]
        if not CourseEnrollment.objects.filter(
            student=request.user,
            course=assignment.course,
            status=CourseEnrollment.Status.ACTIVE,
        ).exists():
            raise PermissionDenied("You must be an active student in this course.")
        with transaction.atomic():
            already_submitted = AssignmentSubmission.objects.filter(
                assignment=assignment,
                student=request.user,
            ).exists()
            submission = serializer.save()
            Grade.objects.filter(
                student=request.user,
                course=assignment.course,
                source_type=Grade.SourceType.ASSIGNMENT,
                source_id=str(submission.pk),
            ).delete()
        return Response(
            AssignmentSubmissionSerializer(submission).data,
            status=status.HTTP_200_OK if already_submitted else status.HTTP_201_CREATED,
        )


class QuizViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Quiz.objects.none()
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Quiz.objects.select_related("course").prefetch_related("questions")
        if user.is_superuser or user.role == User.Role.ADMIN:
            return queryset
        if user.role == User.Role.TEACHER:
            return queryset.filter(course__teacher=user)
        if user.role == User.Role.STUDENT:
            return queryset.filter(course__enrollments__student=user, published=True).distinct()
        if user.role == User.Role.PARENT:
            return queryset.filter(course__enrollments__student__parent_links__parent=user, published=True).distinct()
        return queryset.none()

    @action(detail=True, methods=["post"], url_path="submit")
    def submit(self, request, pk=None):
        quiz = self.get_object()
        serializer = QuizSubmissionSerializer(
            data=request.data,
            context={"quiz": quiz, "request": request},
        )
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            attempt = serializer.save()
            Grade.objects.update_or_create(
                student=request.user,
                course=quiz.course,
                source_type=Grade.SourceType.QUIZ,
                source_id=str(attempt.pk),
                defaults={
                    "score": attempt.score,
                    "graded_by": quiz.course.teacher,
                    "feedback": "",
                },
            )
        return Response(QuizAttemptSerializer(attempt).data, status=status.HTTP_201_CREATED)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Notification.objects.none()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    @action(detail=True, methods=["post"], url_path="read")
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        if notification.read_at is None:
            notification.read_at = timezone.now()
            notification.save(update_fields=["read_at"])
        return Response(self.get_serializer(notification).data)


class ExamViewSet(viewsets.ModelViewSet):
    queryset = Exam.objects.none()
    serializer_class = ExamSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        queryset = Exam.objects.select_related("course", "course__teacher").prefetch_related("questions")
        if user.is_superuser or user.role == User.Role.ADMIN:
            return queryset
        if user.role == User.Role.TEACHER:
            return queryset.filter(course__teacher=user)
        if user.role == User.Role.STUDENT:
            return queryset.filter(
                course__enrollments__student=user,
                course__enrollments__status=CourseEnrollment.Status.ACTIVE,
                published=True,
            ).distinct()
        if user.role == User.Role.PARENT:
            return queryset.filter(
                course__enrollments__student__parent_links__parent=user,
                published=True,
            ).distinct()
        return queryset.none()

    def perform_create(self, serializer):
        user = self.request.user
        course = serializer.validated_data["course"]
        if not user.is_superuser and user.role != User.Role.ADMIN and (
            user.role != User.Role.TEACHER or course.teacher_id != user.pk
        ):
            raise PermissionDenied("You can only create examinations for your own courses.")
        serializer.save()

    def perform_update(self, serializer):
        user = self.request.user
        exam = self.get_object()
        course = serializer.validated_data.get("course", exam.course)
        if not user.is_superuser and user.role != User.Role.ADMIN and (
            user.role != User.Role.TEACHER
            or exam.course.teacher_id != user.pk
            or course.teacher_id != user.pk
        ):
            raise PermissionDenied("You can only update examinations for your own courses.")
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        if not user.is_superuser and user.role != User.Role.ADMIN and (
            user.role != User.Role.TEACHER or instance.course.teacher_id != user.pk
        ):
            raise PermissionDenied("You can only delete examinations for your own courses.")
        instance.delete()

    @action(detail=True, methods=["post"], url_path="start")
    def start(self, request, pk=None):
        exam = self.get_object()
        now = timezone.now()
        if request.user.role != User.Role.STUDENT:
            raise PermissionDenied("Only students can start an examination.")
        if not exam.published or now < exam.starts_at or now > exam.ends_at:
            return Response(
                {"detail": "This examination is not currently open."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not CourseEnrollment.objects.filter(
            student=request.user,
            course=exam.course,
            status=CourseEnrollment.Status.ACTIVE,
        ).exists():
            raise PermissionDenied("You must be actively enrolled in this course.")
        attempt = exam.attempts.filter(student=request.user).first()
        if attempt and attempt.submitted_at:
            return Response(
                {"detail": "You have already submitted this examination."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not attempt:
            attempt = ExamAttempt.objects.create(exam=exam, student=request.user)
        return Response(ExamAttemptSerializer(attempt).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="submit")
    def submit(self, request, pk=None):
        exam = self.get_object()
        with transaction.atomic():
            serializer = ExamSubmissionSerializer(
                data=request.data,
                context={"exam": exam, "request": request},
            )
            serializer.is_valid(raise_exception=True)
            values = serializer.validated_data
            attempt = ExamAttempt.objects.select_for_update().get(pk=values["attempt"].pk)
            if attempt.submitted_at:
                raise PermissionDenied("This examination has already been submitted.")
            questions = list(exam.questions.all())
            points_awarded = sum(
                question.points
                for question in questions
                if values["answers"].get(str(question.pk)) == question.answer
            )
            total_points = sum(question.points for question in questions)
            score = round((points_awarded / total_points) * 100, 2) if total_points else 0
            attempt.answers = values["answers"]
            attempt.score = score
            attempt.submitted_at = timezone.now()
            attempt.save(update_fields=["answers", "score", "submitted_at"])
            Grade.objects.update_or_create(
                student=request.user,
                course=exam.course,
                source_type=Grade.SourceType.EXAM,
                source_id=str(attempt.pk),
                defaults={
                    "score": score,
                    "graded_by": exam.course.teacher,
                    "feedback": "",
                },
            )
        return Response(ExamAttemptSerializer(attempt).data, status=status.HTTP_200_OK)


class ExamQuestionViewSet(viewsets.ModelViewSet):
    queryset = ExamQuestion.objects.none()
    serializer_class = ExamQuestionManagementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = ExamQuestion.objects.select_related("exam", "exam__course")
        if user.is_superuser or user.role == User.Role.ADMIN:
            return queryset
        if user.role == User.Role.TEACHER:
            return queryset.filter(exam__course__teacher=user)
        return queryset.none()

    def perform_create(self, serializer):
        user = self.request.user
        exam = serializer.validated_data["exam"]
        if not user.is_superuser and user.role != User.Role.ADMIN and (
            user.role != User.Role.TEACHER or exam.course.teacher_id != user.pk
        ):
            raise PermissionDenied("You can only manage questions for your own examinations.")
        serializer.save()

    def perform_update(self, serializer):
        user = self.request.user
        question = self.get_object()
        exam = serializer.validated_data.get("exam", question.exam)
        if not user.is_superuser and user.role != User.Role.ADMIN and (
            user.role != User.Role.TEACHER
            or question.exam.course.teacher_id != user.pk
            or exam.course.teacher_id != user.pk
        ):
            raise PermissionDenied("You can only manage questions for your own examinations.")
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        if not user.is_superuser and user.role != User.Role.ADMIN and (
            user.role != User.Role.TEACHER or instance.exam.course.teacher_id != user.pk
        ):
            raise PermissionDenied("You can only manage questions for your own examinations.")
        instance.delete()


class GradeViewSet(viewsets.ModelViewSet):
    queryset = Grade.objects.none()
    serializer_class = GradeSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        queryset = Grade.objects.select_related("student", "course", "graded_by")
        if user.is_superuser or user.role == User.Role.ADMIN:
            return queryset
        if user.role == User.Role.STUDENT:
            return queryset.filter(student=user)
        if user.role == User.Role.PARENT:
            return queryset.filter(student__parent_links__parent=user).distinct()
        if user.role == User.Role.TEACHER:
            return queryset.filter(course__teacher=user)
        return queryset.none()

    def perform_create(self, serializer):
        user = self.request.user
        course = serializer.validated_data["course"]
        student = serializer.validated_data["student"]
        if not user.is_superuser and user.role != User.Role.ADMIN and (
            user.role != User.Role.TEACHER or course.teacher_id != user.pk
        ):
            raise PermissionDenied("Only the course teacher or an administrator can record grades.")
        if not CourseEnrollment.objects.filter(course=course, student=student).exists():
            raise PermissionDenied("The student must be enrolled in this course.")
        serializer.save(graded_by=user)


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.none()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        queryset = Attendance.objects.select_related("course", "student", "recorded_by")
        if user.is_superuser or user.role == User.Role.ADMIN:
            return queryset
        if user.role == User.Role.STUDENT:
            return queryset.filter(student=user)
        if user.role == User.Role.PARENT:
            return queryset.filter(student__parent_links__parent=user).distinct()
        if user.role == User.Role.TEACHER:
            return queryset.filter(course__teacher=user)
        return queryset.none()

    def perform_create(self, serializer):
        user = self.request.user
        course = serializer.validated_data["course"]
        if not user.is_superuser and user.role != User.Role.ADMIN and (
            user.role != User.Role.TEACHER or course.teacher_id != user.pk
        ):
            raise PermissionDenied("Only the course teacher or an administrator can record attendance.")
        serializer.save(recorded_by=user)

    def perform_update(self, serializer):
        user = self.request.user
        attendance = self.get_object()
        course = serializer.validated_data.get("course", attendance.course)
        if not user.is_superuser and user.role != User.Role.ADMIN and (
            user.role != User.Role.TEACHER
            or attendance.course.teacher_id != user.pk
            or course.teacher_id != user.pk
        ):
            raise PermissionDenied("Only the course teacher can update this attendance record.")
        serializer.save()


class CalendarEventViewSet(viewsets.ModelViewSet):
    queryset = CalendarEvent.objects.none()
    serializer_class = CalendarEventSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["starts_at", "ends_at"]
    ordering = ["starts_at"]

    def get_queryset(self):
        user = self.request.user
        queryset = CalendarEvent.objects.select_related("course", "created_by")
        public_events = Q(course__isnull=True)
        if user.is_superuser or user.role == User.Role.ADMIN:
            return queryset
        if user.role == User.Role.STUDENT:
            return queryset.filter(public_events | Q(course__enrollments__student=user)).distinct()
        if user.role == User.Role.PARENT:
            return queryset.filter(public_events | Q(course__enrollments__student__parent_links__parent=user)).distinct()
        if user.role == User.Role.TEACHER:
            return queryset.filter(public_events | Q(course__teacher=user)).distinct()
        return queryset.none()

    def perform_create(self, serializer):
        user = self.request.user
        course = serializer.validated_data.get("course")
        if not course and user.role != User.Role.ADMIN and not user.is_superuser:
            raise PermissionDenied("Only administrators can create events for the whole platform.")
        if course and not user.is_superuser and user.role != User.Role.ADMIN and (
            user.role != User.Role.TEACHER or course.teacher_id != user.pk
        ):
            raise PermissionDenied("You can only create events for your own courses.")
        serializer.save(created_by=user)

    def perform_update(self, serializer):
        user = self.request.user
        event = self.get_object()
        course = serializer.validated_data.get("course", event.course)
        if not user.is_superuser and user.role != User.Role.ADMIN and (
            user.role != User.Role.TEACHER
            or event.created_by_id != user.pk
            or (course and course.teacher_id != user.pk)
            or (course is None)
        ):
            raise PermissionDenied("You can only update events you created for your own courses.")
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        if not user.is_superuser and user.role != User.Role.ADMIN and (
            user.role != User.Role.TEACHER
            or instance.created_by_id != user.pk
            or not instance.course_id
        ):
            raise PermissionDenied("You can only delete events you created for your own courses.")
        instance.delete()


class ConversationViewSet(viewsets.ModelViewSet):
    queryset = Conversation.objects.none()
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [MessagingThrottle]
    http_method_names = ["get", "post", "head", "options"]
    filter_backends = [filters.SearchFilter]
    search_fields = ["title", "course__title", "participants__first_name", "participants__last_name"]

    def get_serializer_class(self):
        if self.action == "create":
            return ConversationCreateSerializer
        return ConversationSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Conversation.objects.select_related("course").prefetch_related("participants")
        if user.is_superuser or user.role == User.Role.ADMIN:
            return queryset
        return queryset.filter(participants=user).distinct()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        conversation = serializer.save()
        return Response(
            ConversationSerializer(conversation).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get", "post"], url_path="messages")
    def messages(self, request, pk=None):
        conversation = self.get_object()
        if request.method == "GET":
            Message.objects.filter(
                conversation=conversation,
                read_at__isnull=True,
            ).exclude(sender=request.user).update(read_at=timezone.now())
            messages = Message.objects.filter(conversation=conversation).select_related("sender").order_by("-sent_at")
            page = self.paginate_queryset(messages)
            if page is not None:
                return self.get_paginated_response(MessageSerializer(page, many=True).data[::-1])
            return Response(MessageSerializer(messages, many=True).data[::-1])

        serializer = MessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            message = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                body=serializer.validated_data["body"],
            )
            conversation.updated_at = message.sent_at
            conversation.save(update_fields=["updated_at"])
            Notification.objects.bulk_create([
                Notification(
                    recipient=participant,
                    title=f"New message from {request.user.get_full_name() or request.user.username}",
                    message=message.body[:500],
                    kind="message",
                )
                for participant in conversation.participants.exclude(pk=request.user.pk)
            ])
        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)


class MessageContactsView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [MessagingThrottle]

    @extend_schema(responses=UserSerializer(many=True))
    def get(self, request):
        raw_course_id = request.query_params.get("course")
        if not raw_course_id:
            return Response(
                {"course": "A course ID is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            course_id = int(raw_course_id)
        except ValueError:
            return Response(
                {"course": "Provide a valid course ID."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = request.user
        course = Course.objects.filter(pk=course_id).first()
        if not course:
            return Response({"detail": "Course not found."}, status=status.HTTP_404_NOT_FOUND)

        if user.is_superuser or user.role == User.Role.ADMIN:
            contacts = User.objects.filter(
                is_active=True,
                role__in=[User.Role.STUDENT, User.Role.PARENT, User.Role.TEACHER],
            ).exclude(pk=user.pk)
        elif user.role == User.Role.TEACHER and course.teacher_id == user.pk:
            contacts = User.objects.filter(
                Q(course_enrollments__course=course, course_enrollments__status=CourseEnrollment.Status.ACTIVE)
                | Q(
                    child_links__student__course_enrollments__course=course,
                    child_links__student__course_enrollments__status=CourseEnrollment.Status.ACTIVE,
                ),
                is_active=True,
            ).exclude(pk=user.pk).distinct()
        elif user.role == User.Role.STUDENT and CourseEnrollment.objects.filter(
            student=user,
            course=course,
            status=CourseEnrollment.Status.ACTIVE,
        ).exists():
            contacts = User.objects.filter(pk=course.teacher_id, is_active=True)
        elif user.role == User.Role.PARENT and StudentParent.objects.filter(
            parent=user,
            student__course_enrollments__course=course,
            student__course_enrollments__status=CourseEnrollment.Status.ACTIVE,
        ).exists():
            contacts = User.objects.filter(pk=course.teacher_id, is_active=True)
        else:
            raise PermissionDenied("You do not have access to message contacts for this course.")

        return Response(MessageParticipantSerializer(contacts.order_by("first_name", "last_name"), many=True).data)


class ParentChildrenView(APIView):
    permission_classes = [ParentPermission]

    @extend_schema(responses=StudentParentSerializer(many=True))
    def get(self, request):
        links = StudentParent.objects.filter(parent=request.user).select_related("student")
        return Response(StudentParentSerializer(links, many=True).data)
