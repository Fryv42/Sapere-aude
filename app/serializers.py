"""
Сериализаторы Django REST Framework для моделей квизов.
"""
from rest_framework import serializers
from .models import Quiz, Question, AnswerOption, QuizSession, Participant

class AnswerOptionSerializer(serializers.ModelSerializer):
    """Сериализатор для вариантов ответов."""
    class Meta:
        model = AnswerOption
        fields = ['id', 'text', 'is_correct']


class QuestionSerializer(serializers.ModelSerializer):
    """Сериализатор для вопросов (только чтение)."""
    answers = AnswerOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'quiz', 'text', 'order', 'timer_seconds', 'answers']


class QuestionCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания вопросов внутри квиза."""

    class Meta:
        model = Question
        fields = ['text', 'order', 'timer_seconds']


class QuizSerializer(serializers.ModelSerializer):
    """Сериализатор для викторин (только чтение)."""
    questions = QuestionSerializer(many=True, read_only=True)
    created_by = serializers.ReadOnlyField(source='created_by.username')

    class Meta:
        model = Quiz
        fields = [
            'id', 'title', 'description', 'created_by',
            'created_at', 'is_active', 'questions'
        ]


class QuizWriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания и обновления викторин.

    Используется для POST/PUT/PATCH операций с вложенными вопросами.
    """
    questions = QuestionCreateSerializer(many=True)
    created_by = serializers.ReadOnlyField(source='created_by.username')

    class Meta:
        model = Quiz
        fields = [
            'id',
            'title',
            'description',
            'created_by',
            'created_at',
            'is_active',
            'questions',
        ]
        read_only_fields = ['created_at']

    def validate(self, attrs):
        """
        Проверяет наличие хотя бы одного вопроса при создании квиза.
        """
        request = self.context.get('request')
        if request and request.method == 'POST':
            questions = attrs.get('questions') or []
            if not questions:
                raise serializers.ValidationError(
                    {"questions": "При создании викторины должен быть как минимум один вопрос."}
                )
        return attrs

    def create(self, validated_data):
        questions_data = validated_data.pop('questions', [])
        quiz = Quiz.objects.create(**validated_data)
        for index, question_data in enumerate(questions_data):
            Question.objects.create(
                quiz=quiz,
                text=question_data.get('text'),
                order=question_data.get('order', index),
                timer_seconds=question_data.get('timer_seconds'),
            )
        return quiz

    def update(self, instance, validated_data):
        """
        Обновляет только поля квиза.

        Вопросы при обновлении этого endpoint не изменяются.
        """
        validated_data.pop('questions', None)
        for field in ['title', 'description', 'is_active']:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()
        return instance


class ParticipantSerializer(serializers.ModelSerializer):
    """Сериализатор для участников."""
    class Meta:
        model = Participant
        fields = ['id', 'session', 'name', 'joined_at', 'total_score']


class QuizSessionSerializer(serializers.ModelSerializer):
    """Сериализатор для сессий."""
    quiz_title = serializers.ReadOnlyField(source='quiz.title')
    participants = ParticipantSerializer(many=True, read_only=True)

    class Meta:
        model = QuizSession
        fields = [
            'id', 'quiz', 'quiz_title', 'session_code',
            'started_at', 'ended_at', 'is_active', 'participants'
        ]
