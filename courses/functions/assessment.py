from courses.models.assessment import Assessment, AssessmentQuestion
from courses.serializers import AssessmentSerializer, AssessmentQuestionSerializer
from courses.models.course import Course
from rest_framework.response import Response
from rest_framework import status
import json

def PostAssessment(self, request):
    course_id = self.kwargs.get('course_id')
    try:
        course = Course.objects.get(pk=course_id)
    except Course.DoesNotExist:
        return Response({"error": "Course not found"}, status=status.HTTP_404_NOT_FOUND)

    assessment, created = Assessment.objects.get_or_create(course=course)
    
    # Handle Assessment fields
    data = request.data
    assessment.title = data.get('title', assessment.title or f"Final Exam for {course.title}")
    assessment.description = data.get('description', assessment.description)
    assessment.time_limit_minutes = data.get('time_limit_minutes', assessment.time_limit_minutes)
    assessment.passing_score = data.get('passing_score', assessment.passing_score)
    assessment.max_attempts = data.get('max_attempts', assessment.max_attempts)
    assessment.save()

    # Handle Questions if provided (could be a separate API but good to have here for bulk update)
    questions_data = data.get('questions')
    if questions_data:
        if isinstance(questions_data, str):
            questions_data = json.loads(questions_data)
        
        # Simple implementation: Update/Create questions
        # For a full implementation, you might want to handle deletion of old questions too
        for q_data in questions_data:
            q_id = q_data.get('id')
            if q_id:
                try:
                    question = AssessmentQuestion.objects.get(pk=q_id, assessment=assessment)
                except AssessmentQuestion.DoesNotExist:
                    continue
            else:
                question = AssessmentQuestion(assessment=assessment)
            
            question.text = q_data.get('text', question.text)
            question.question_type = q_data.get('question_type', question.question_type)
            question.options = q_data.get('options', question.options)
            question.correct_answer = q_data.get('correct_answer', question.correct_answer)
            question.points = q_data.get('points', question.points)
            question.order = q_data.get('order', question.order)
            question.save()

    serializer = AssessmentSerializer(assessment)
    return Response(serializer.data, status=status.HTTP_200_OK)

def DeleteAssessmentQuestion(self, request):
    q_id = self.kwargs.get('id')
    try:
        question = AssessmentQuestion.objects.get(pk=q_id)
        question.is_deleted = True
        question.save()
        return Response({"message": "Question deleted successfully", "result": True})
    except AssessmentQuestion.DoesNotExist:
        return Response({"error": "Question not found"}, status=status.HTTP_404_NOT_FOUND)
