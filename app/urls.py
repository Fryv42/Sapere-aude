from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import QuizViewSet, QuizSessionViewSet, health_check, get_version

router = DefaultRouter()
router.register(r'quizzes', QuizViewSet)
router.register(r'sessions', QuizSessionViewSet)

urlpatterns = [
    path('health/', health_check),
    path('version/', get_version),
    path('', include(router.urls)),
]
