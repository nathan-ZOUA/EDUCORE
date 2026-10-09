from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    AssignmentSubmissionViewSet,
    AssignmentViewSet,
    AdminUserViewSet,
    BookViewSet,
    ConversationViewSet,
    CourseViewSet,
    CurrentUserView,
    DashboardView,
    EDUCORETokenObtainPairView,
    EnrollmentViewSet,
    ExamQuestionViewSet,
    ExamViewSet,
    GradeViewSet,
    AttendanceViewSet,
    CalendarEventViewSet,
    LessonProgressViewSet,
    LessonViewSet,
    MessageContactsView,
    NotificationViewSet,
    ParentChildrenView,
    ProfilePhotoViewSet,
    QuizViewSet,
    RegistrationView,
    SubjectViewSet,
    health_check,
)

router = DefaultRouter()
router.register("courses", CourseViewSet, basename="course")
router.register("enrollments", EnrollmentViewSet, basename="enrollment")
router.register("lessons", LessonViewSet, basename="lesson")
router.register("lesson-progress", LessonProgressViewSet, basename="lesson-progress")
router.register("books", BookViewSet, basename="book")
router.register("assignments", AssignmentViewSet, basename="assignment")
router.register("submissions", AssignmentSubmissionViewSet, basename="submission")
router.register("quizzes", QuizViewSet, basename="quiz")
router.register("notifications", NotificationViewSet, basename="notification")
router.register("subjects", SubjectViewSet, basename="subject")
router.register("exams", ExamViewSet, basename="exam")
router.register("exam-questions", ExamQuestionViewSet, basename="exam-question")
router.register("grades", GradeViewSet, basename="grade")
router.register("attendance", AttendanceViewSet, basename="attendance")
router.register("calendar", CalendarEventViewSet, basename="calendar")
router.register("conversations", ConversationViewSet, basename="conversation")
router.register("profile/photos", ProfilePhotoViewSet, basename="profile-photo")
router.register("admin/users", AdminUserViewSet, basename="admin-user")

urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("auth/register/", RegistrationView.as_view(), name="register"),
    path("auth/token/", EDUCORETokenObtainPairView.as_view(), name="token-obtain"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("auth/me/", CurrentUserView.as_view(), name="current-user"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("parent/children/", ParentChildrenView.as_view(), name="parent-children"),
    path("message-contacts/", MessageContactsView.as_view(), name="message-contacts"),
    path("", include(router.urls)),
]
