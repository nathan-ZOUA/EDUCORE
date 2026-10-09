from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    Assignment,
    AssignmentSubmission,
    Attendance,
    AuditLog,
    Book,
    BookCategory,
    Bookmark,
    CalendarEvent,
    Conversation,
    Course,
    CourseEnrollment,
    Exam,
    ExamAttempt,
    ExamQuestion,
    Grade,
    Lesson,
    LessonProgress,
    Message,
    Notification,
    ParentProfile,
    ProfilePhoto,
    Question,
    Quiz,
    QuizAttempt,
    StudentParent,
    StudentProfile,
    Subject,
    TeacherProfile,
    User,
)


@admin.register(User)
class EDUCOREUserAdmin(UserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "role", "is_active")
    list_filter = ("role", "is_active", "is_staff")
    fieldsets = UserAdmin.fieldsets + (("EDUCORE", {"fields": ("role",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("EDUCORE", {"fields": ("email", "role")}),)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "subject", "teacher", "academic_level", "status")
    list_filter = ("status", "subject", "academic_level")
    search_fields = ("title", "description", "teacher__email")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(BookCategory)
class BookCategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "subject", "category", "academic_level")
    list_filter = ("subject", "category", "academic_level")
    search_fields = ("title", "author", "description")


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "due_at", "max_score")
    list_filter = ("course",)
    search_fields = ("title", "course__title")


@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ("assignment", "student", "status", "score", "submitted_at")
    list_filter = ("status",)
    search_fields = ("assignment__title", "student__email")


admin.site.register(
    (
        StudentProfile,
        ParentProfile,
        ProfilePhoto,
        TeacherProfile,
        StudentParent,
        CourseEnrollment,
        Lesson,
        LessonProgress,
        Bookmark,
        Quiz,
        Question,
        QuizAttempt,
        Notification,
        AuditLog,
        Exam,
        ExamQuestion,
        ExamAttempt,
        Grade,
        Attendance,
        CalendarEvent,
        Conversation,
        Message,
    )
)
