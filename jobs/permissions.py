from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsEmployer(BasePermission):
    message = "An employer profile is required."
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and hasattr(request.user, "employer_profile"))

class IsCandidate(BasePermission):
    message = "A candidate profile is required."
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and hasattr(request.user, "candidate_profile"))

class IsApplicationParticipant(BasePermission):
    def has_object_permission(self, request, view, obj):
        return (
            obj.candidate.user_id == request.user.id
            or obj.job.employer.user_id == request.user.id
        )
