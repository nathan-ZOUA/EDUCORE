from django.db.models import Q
from rest_framework.permissions import SAFE_METHODS, BasePermission

from .models import CourseEnrollment, StudentParent, User


def user_can_access_course(user, course):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser or user.role == User.Role.ADMIN:
        return True
    if user.role == User.Role.TEACHER:
        return course.teacher_id == user.pk
    if user.role == User.Role.STUDENT:
        return CourseEnrollment.objects.filter(student=user, course=course).exists()
    if user.role == User.Role.PARENT:
        return StudentParent.objects.filter(
            parent=user,
            student__course_enrollments__course=course,
        ).exists()
    return False


class CoursePermission(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_superuser or request.user.role in [User.Role.ADMIN, User.Role.TEACHER])
        )

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return obj.status == obj.Status.PUBLISHED or user_can_access_course(request.user, obj)
        if request.user.is_superuser or request.user.role == User.Role.ADMIN:
            return True
        return request.user.role == User.Role.TEACHER and obj.teacher_id == request.user.pk


class CourseContentPermission(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_superuser or request.user.role in [User.Role.ADMIN, User.Role.TEACHER])
        )

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser or request.user.role == User.Role.ADMIN:
            return True
        if request.user.role == User.Role.TEACHER:
            return obj.course.teacher_id == request.user.pk
        return request.method in SAFE_METHODS and user_can_access_course(request.user, obj.course)


class ParentPermission(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == User.Role.PARENT
        )


class EDUCOREAdminPermission(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_superuser or request.user.role == User.Role.ADMIN)
        )
