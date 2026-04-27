
from rest_framework import serializers
from .models import Quiz, Question, AnswerOption, QuizSession, Participant
from django.core.exceptions import ValidationError


class AnswerOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerOption
        fields = ['id', 'text', 'is_correct']

    def validate(self, data):
        return data


class QuestionSerializer(serializers.ModelSerializer):
    answer_options = AnswerOptionSerializer(many=True)

    class Meta:
        model = Question
        fields = ['id', 'text', 'question_type', 'points', 'answer_options']

    def validate_answer_options(self, value):
        if len(value) < 2:
            raise serializers.ValidationError(
                "Вопрос должен содержать минимум 2 варианта ответа."
            )
        return value

    def validate(self, data):
        answer_options = data.get('answer_options', [])

        if answer_options:
            correct_count = sum(1 for opt in answer_options if opt.get('is_correct'))
            if correct_count == 0:
                raise serializers.ValidationError(
                    {"answer_options": "Хотя бы один вариант ответа должен быть правильным."}
                )

            if data.get('question_type') == 'single' and correct_count != 1:
                raise serializers.ValidationError(
                    {"answer_options": "Для вопроса с одиночным выбором должен быть ровно один правильный ответ."}
                )

        return data

    def create(self, validated_data):
        answer_options_data = validated_data.pop('answer_options')
        question = Question.objects.create(**validated_data)

        for option_data in answer_options_data:
            AnswerOption.objects.create(question=question, **option_data)

        return question

    def update(self, instance, validated_data):
        answer_options_data = validated_data.pop('answer_options', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if answer_options_data is not None:
            instance.answer_options.all().delete()
            for option_data in answer_options_data:
                AnswerOption.objects.create(question=instance, **option_data)

        return instance


class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=False)

    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description', 'created_by', 'created_at',
                  'updated_at', 'is_published', 'questions']
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def validate_questions(self, value):
        if len(value) < 1:
            raise serializers.ValidationError(
                "Квиз должен содержать минимум 1 вопрос."
            )
        return value

    def validate(self, data):
        questions = data.get('questions', [])

        question_texts = [q.get('text') for q in questions]
        if len(question_texts) != len(set(question_texts)):
            raise serializers.ValidationError(
                {"questions": "Вопросы в квизе должны быть уникальны."}
            )

        return data

    def create(self, validated_data):
        questions_data = validated_data.pop('questions')
        quiz = Quiz.objects.create(**validated_data)

        for question_data in questions_data:
            QuestionSerializer().create({
                **question_data,
                'quiz': quiz
            })

        return quiz

    def update(self, instance, validated_data):
        questions_data = validated_data.pop('questions', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if questions_data is not None:
            instance.questions.all().delete()
            for question_data in questions_data:
                QuestionSerializer().create({
                    **question_data,
                    'quiz': instance
                })

        return instance


class ParticipantSerializer(serializers.ModelSerializer):

    class Meta:
        model = Participant
        fields = ['id', 'user', 'name', 'email']
        read_only_fields = ['id']

    def validate_email(self, value):
        if value and '@' not in value:
            raise serializers.ValidationError("Введите корректный email.")
        return value


class QuizSessionSerializer(serializers.ModelSerializer):
    participant = ParticipantSerializer(read_only=False)

    class Meta:
        model = QuizSession
        fields = ['id', 'quiz', 'participant', 'started_at', 'completed_at',
                  'score', 'is_active', 'session_key']
        read_only_fields = ['id', 'started_at', 'completed_at', 'score',
                           'is_active', 'session_key']

    def validate(self, data):
        quiz = data.get('quiz')
        participant_data = data.get('participant')

        if quiz and not quiz.is_published:
            raise serializers.ValidationError(
                {"quiz": "Нельзя начать сессию для неопубликованного квиза."}
            )

        return data

    def create(self, validated_data):
        participant_data = validated_data.pop('participant')
        participant, created = Participant.objects.get_or_create(
            **participant_data
        )

        quiz_session = QuizSession.objects.create(
            participant=participant,
            **validated_data
        )

        return quiz_session

    def update(self, instance, validated_data):
        participant_data = validated_data.pop('participant', None)

        if participant_data:
            for attr, value in participant_data.items():
                setattr(instance.participant, attr, value)
            instance.participant.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance

class QuizReadOnlySerializer(QuizSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta(QuizSerializer.Meta):
        fields = QuizSerializer.Meta.fields + ['total_questions', 'total_points']

    def get_total_questions(self, obj):
        return obj.questions.count()

    def get_total_points(self, obj):
        return sum(question.points for question in obj.questions.all())


class QuizSessionReadOnlySerializer(QuizSessionSerializer):
    participant = ParticipantSerializer(read_only=True)
    quiz = QuizReadOnlySerializer(read_only=True)

    class Meta(QuizSessionSerializer.Meta):
        fields = QuizSessionSerializer.Meta.fields + ['duration_seconds', 'completion_percentage']

    def get_duration_seconds(self, obj):
        if obj.completed_at and obj.started_at:
            return (obj.completed_at - obj.started_at).total_seconds()
        return None

    def get_completion_percentage(self, obj):
        return 0  

