"""
Представления (views) для API квизов.
Используется Django REST Framework для создания API endpoints.
"""
import logging
from django.db import IntegrityError
from rest_framework import viewsets, status, filters
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from .models import Quiz, QuizSession, Participant
from .serializers import QuizSerializer, QuizSessionSerializer, ParticipantSerializer
from .factories import SessionCodeFactory
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .services import generate_session_csv

logger = logging.getLogger(__name__) # [cite: 1]
logger = logging.getLogger('app.views')


@api_view(['GET'])
def health_check(request):
    """
    Проверка работоспособности сервиса.

    Returns:
        Response: Статус "ok" если приложение работает
    """
    logger.info("Health check requested")
    return Response({"status": "ok"})


@api_view(['GET'])
def get_version(request):
    """
    Получить информацию о версии приложения.

    Returns:
        Response: Название и версия приложения
    """
    return Response({
        "app_name": "Quiz Service",
        "version": "0.1.0",
        "framework": "Django 4.2"
    })


class QuizViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления викторинами.

    list: GET /api/v1/quizzes/ - список всех квизов
    retrieve: GET /api/v1/quizzes/{id}/ - детальная информация
    create: POST /api/v1/quizzes/ - создание квиза
    update: PUT /api/v1/quizzes/{id}/ - обновление квиза
    destroy: DELETE /api/v1/quizzes/{id}/ - удаление квиза
    """
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'title']
    ordering = ['-created_at']
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']

    def perform_create(self, serializer):
        """Сохраняет викторину с текущим пользователем как создателем."""
        serializer.save(created_by=self.request.user)
        logger.info("Quiz created by user: %s", self.request.user.username)

    @action(detail=True, methods=['post'])
    def start_session(self, request, pk=None):
        """Запустить новую сессию для викторины."""
        quiz = self.get_object()

        for _ in range(5):  # retry mechanism
            try:
                session = QuizSession.objects.create(
                    quiz=quiz,
                    session_code=SessionCodeFactory.create()
                )
                logger.info("Session started for quiz: %s", quiz.title)
                return Response(QuizSessionSerializer(session).data)

            except IntegrityError:
                logger.warning("Session code collision, retrying...")

        return Response(
            {"error": "Could not generate unique session code"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class QuizSessionViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления сессиями квизов.

    list: GET /api/v1/sessions/ – список сессий
    retrieve: GET /api/v1/sessions/{id}/ – детальная информация
    create: POST /api/v1/sessions/ – создание сессии
    update: PUT /api/v1/sessions/{id}/ – обновление сессии
    destroy: DELETE /api/v1/sessions/{id}/ – удаление сессии
    join: POST /api/v1/sessions/{id}/join/ – присоединиться к сессии
    """
    queryset = QuizSession.objects.all().prefetch_related('participants')
    serializer_class = QuizSessionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['is_active', 'quiz']
    search_fields = ['session_code']

    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """
        Участник присоединяется к сессии.

        Требования:
        - Сессия должна быть активной.
        - Имя участника берётся из request.data['name'], минимум 2 символа.
        - Имя должно быть уникальным в рамках одной сессии.
        """
        session = self.get_object()

        if not session.is_active:
            return Response(
                {"error": "Session is closed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        participant = Participant.objects.create(
            session=session,
            name=request.data['name'] # name=name,
        )
        logger.info(
            "Participant '%s' joined session: %s",
            participant.name,
            session.session_code,
        )

        logger.info("Participant joined session: %s", session.session_code)

        return Response(ParticipantSerializer(participant).data)
    

class ExportSessionResultsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        session = get_object_or_404(QuizSession, id=session_id)
        csv_content = generate_session_csv(session)
        
        response = HttpResponse(csv_content, content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="results_{session.session_code}.csv"'
        
        logger.info(f"Export CSV: session {session_id} by user {request.user.id}") # [cite: 1]
        return response
    