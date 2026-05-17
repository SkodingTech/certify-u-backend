"""Seed minimal but comprehensive test data for API testing."""
import os, django, sys
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "certifyu.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from users.models.user import UserProfile, StudentProfile, InstructorProfile
from courses.models.category import Category
from courses.models.organizer import Organization
from courses.models.course import Course, Module, Lesson, CourseResource, Discussion
from courses.models.instructor import Instructor
from courses.models.assessment import Assessment, AssessmentQuestion
from courses.models.review import Review
from courses.models.live_session import LiveSession
from courses.models.booking import TrainerAvailability, Slot, Booking
from courses.models.job_role import JobRole
from courses.models.support import SupportChannel, SupportTicket
from courses.models.regulatory import RegulatoryAuthority
from api.models import Blogs, NewsLetter, HeroSection, FunFact, Testimonial, Brand, LegalDocs, Messages

User = get_user_model()
log = lambda m: print(f"[seed] {m}")

# --- Users ---
def get_or_create_user(username, email, password, **extra):
    u, c = User.objects.get_or_create(username=username, defaults={"email": email, **extra})
    if c:
        u.set_password(password); u.save()
    return u

admin = get_or_create_user("admin", "admin@certify-u.test", "AdminPass123!", is_staff=True, is_superuser=True)
log(f"admin: {admin.username}")
student = get_or_create_user("student1", "student1@certify-u.test", "StudPass123!")
instr_user = get_or_create_user("instructor1", "instr1@certify-u.test", "InstrPass123!")

UserProfile.objects.get_or_create(user=admin, defaults={"role": "SuperAdmin"})
UserProfile.objects.get_or_create(user=student, defaults={"role": "Student"})
UserProfile.objects.get_or_create(user=instr_user, defaults={"role": "Instructor"})
StudentProfile.objects.get_or_create(user=student)
InstructorProfile.objects.get_or_create(user=instr_user)

# --- Categories ---
cat_tech, _ = Category.objects.get_or_create(name="Technology", defaults={"slug": "technology", "description": "Tech courses"})
cat_health, _ = Category.objects.get_or_create(name="Healthcare", defaults={"slug": "healthcare", "description": "Healthcare"})
log(f"categories: {Category.objects.count()}")

# --- Organization ---
org, _ = Organization.objects.get_or_create(name="Certify-U Academy", defaults={"description": "Primary org"})

# --- Regulatory ---
reg, _ = RegulatoryAuthority.objects.get_or_create(name="KHDA", defaults={"country": "UAE", "description": "Dubai KHDA"})

# --- Instructor model ---
instr, _ = Instructor.objects.get_or_create(user=instr_user, defaults={
    "title": "Senior Trainer", "bio": "10 yrs experience", "verified": True,
    "verification_status": "approved",
})

# --- Courses ---
def make_course(title, slug, **kw):
    c, created = Course.objects.get_or_create(slug=slug, defaults={
        "title": title, "subtitle": title + " subtitle",
        "description": "A comprehensive course.", "short_description": "Short.",
        "course_type": "training", "delivery_mode": "online",
        "level": "beginner", "status": "published",
        "language": "English", "duration_weeks": 4, "weekly_hours": 5,
        "price": 199, "currency": "AED",
        "has_certificate": True, "is_approved": True,
        "organization": org, "featured": True,
        "published_at": timezone.now(),
        **kw,
    })
    if created:
        c.categories.add(cat_tech)
        c.instructors.add(instr)
    return c

c1 = make_course("Flutter for Beginners", "flutter-beginners")
c2 = make_course("Advanced Python", "advanced-python")
c3 = make_course("Patient Care Basics", "patient-care", level="intermediate")
log(f"courses: {Course.objects.count()}")

# --- Modules + Lessons ---
for i, course in enumerate([c1, c2, c3], 1):
    for mi in range(1, 3):
        m, _ = Module.objects.get_or_create(course=course, order=mi, defaults={
            "title": f"Module {mi}", "description": f"Module {mi} desc",
            "duration_hours": 2,
        })
        for li in range(1, 3):
            Lesson.objects.get_or_create(module=m, order=li, defaults={
                "title": f"Lesson {mi}.{li}", "description": "desc",
                "lesson_type": "video", "video_url": "https://example.com/v.mp4",
                "video_duration": 600, "is_free": li == 1,
            })

# --- Assessments ---
for course in [c1, c2]:
    a, _ = Assessment.objects.get_or_create(course=course, defaults={
        "title": f"{course.title} Exam", "description": "Final exam",
        "time_limit_minutes": 30, "passing_score": 60, "max_attempts": 3,
    })
    AssessmentQuestion.objects.get_or_create(assessment=a, order=1, defaults={
        "text": "What is 2+2?", "question_type": "mcq",
        "options": [{"id": "a", "text": "3"}, {"id": "b", "text": "4"}],
        "correct_answer": "b", "points": 10,
    })
log(f"assessments: {Assessment.objects.count()}")

# --- Job roles ---
JobRole.objects.get_or_create(title="Mobile Developer", defaults={
    "description": "Build mobile apps", "salary_min": 8000, "salary_max": 15000,
    "salary_currency": "AED", "salary_period": "monthly", "region": "UAE",
})

# --- Live Session ---
LiveSession.objects.get_or_create(course=c1, title="Live Q&A", defaults={
    "instructor": instr, "description": "Q&A session",
    "session_type": "online", "start_time": timezone.now() + timedelta(days=2),
    "end_time": timezone.now() + timedelta(days=2, hours=1),
    "status": "scheduled", "meeting_link": "https://zoom.us/j/123",
})

# --- Trainer availability + Slot ---
TrainerAvailability.objects.get_or_create(instructor=instr, day_of_week=1, defaults={
    "start_time": "09:00", "end_time": "17:00", "timezone": "Asia/Dubai",
})
slot, _ = Slot.objects.get_or_create(course=c1, instructor=instr,
    start_time=timezone.now() + timedelta(days=3),
    defaults={
        "mode": "online", "end_time": timezone.now() + timedelta(days=3, hours=1),
        "capacity": 10, "status": "open",
    })

# --- Support ---
SupportChannel.objects.get_or_create(channel_type="email", value="support@certify-u.test",
    defaults={"label": "Support Email", "is_published": True})
SupportChannel.objects.get_or_create(channel_type="whatsapp", value="+971501234567",
    defaults={"label": "WhatsApp", "is_published": True})

# --- Reviews ---
Review.objects.get_or_create(student=student, course=c1, defaults={
    "rating": 5, "title": "Excellent", "comment": "Loved this course.",
})

# --- API app content ---
HeroSection.objects.get_or_create(title="Learn Anywhere", defaults={
    "subtitle": "Become a certified pro", "button_text": "Start now",
})
FunFact.objects.get_or_create(title="Students", defaults={
    "description": "Active learners", "icon": "fa-user", "count": "10k+",
})
Testimonial.objects.get_or_create(name="Aisha", defaults={
    "position": "Nurse", "testimonial": "Great platform!", "rating": 5,
})
Brand.objects.get_or_create(name="ACME", defaults={"url": "https://acme.test"})
Blogs.objects.get_or_create(name="Welcome", defaults={"content": "<p>Hello world</p>"})
NewsLetter.objects.get_or_create(email="news@certify-u.test", defaults={"name": "News Sub"})
LegalDocs.objects.get_or_create(id=1, defaults={
    "terms": "<p>Terms</p>", "privacy": "<p>Privacy</p>",
    "refund": "<p>Refund</p>", "cookies": "<p>Cookies</p>",
})
Messages.objects.get_or_create(id=1, defaults={"meta_data": {"name": "Test Contact"}})

log("=== Summary ===")
log(f"users: {User.objects.count()}")
log(f"categories: {Category.objects.count()}")
log(f"courses: {Course.objects.count()}")
log(f"modules: {Module.objects.count()}")
log(f"lessons: {Lesson.objects.count()}")
log(f"assessments: {Assessment.objects.count()}")
log(f"instructors: {Instructor.objects.count()}")
log(f"live sessions: {LiveSession.objects.count()}")
log(f"slots: {Slot.objects.count()}")
log(f"job_roles: {JobRole.objects.count()}")
log(f"support_channels: {SupportChannel.objects.count()}")
log(f"blogs: {Blogs.objects.count()}")
log(f"testimonials: {Testimonial.objects.count()}")
log("done.")
