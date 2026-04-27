import csv
import io
from django.db.models import Count, Q

def generate_session_csv(session):
    output = io.StringIO()
    output.write('\ufeff')  
    
    writer = csv.writer(output)
    writer.writerow(['Имя', 'Общий балл', 'Правильные ответы', 'Время последнего ответа']) # [cite: 1]

    
    participants = session.participants.annotate(
        correct_count=Count('answers', filter=Q(answers__is_correct=True))
    ).order_by('-total_score')

    for p in participants:
        last_resp = p.answers.order_by('-answered_at').first()
        time_str = last_resp.answered_at.strftime('%Y-%m-%d %H:%M') if last_resp else "—"
        
        writer.writerow([p.name, p.total_score, p.correct_count, time_str]) # [cite: 1]
    
    return output.getvalue()


