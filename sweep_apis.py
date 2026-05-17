"""Hit every documented endpoint and record status code + verdict."""
import json
import urllib.request
import urllib.error
import urllib.parse
import sys

BASE = "http://127.0.0.1:8765"
ADMIN_TOK = "test-admin-token-xyz"
STUDENT_TOK = "test-student-token-xyz"

def call(method, path, token=ADMIN_TOK, body=None, content_type="application/json"):
    url = BASE + path
    data = None
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    if body is not None:
        if content_type == "application/json":
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        else:
            data = urllib.parse.urlencode(body).encode()
            headers["Content-Type"] = content_type
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            body = r.read().decode("utf-8", errors="replace")
            return r.status, body[:200]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return e.code, body[:200]
    except Exception as e:
        return 0, str(e)[:200]

# Endpoint list: (label, method, path, body)
ENDPOINTS = [
    # --- API app (content) ---
    ("api: BlogsListView", "GET", "/api/BlogsListView", None),
    ("api: BrandListView", "GET", "/api/BrandListView", None),
    ("api: FunFactListView", "GET", "/api/FunFactListView", None),
    ("api: HeroSectionListView", "GET", "/api/HeroSectionListView", None),
    ("api: TestimonialListView", "GET", "/api/TestimonialListView", None),
    ("api: NewsLetterListView", "GET", "/api/NewsLetterListView", None),
    ("api: LegalDocsListView", "GET", "/api/LegalDocsListView", None),
    ("api: MessagesListView", "GET", "/api/MessagesListView", None),
    ("api: GetCountsAPIView", "GET", "/api/GetCountsAPIView", None),
    ("api: BlogsAPIView(detail)", "GET", "/api/1/BlogsAPIView", None),
    ("api: LegalDocsAPIView(detail)", "GET", "/api/1/LegalDocsAPIView", None),
    ("api: CreateNewsLetter", "POST", "/api/CreateNewsLetter",
        {"email": "new@certify-u.test", "name": "New"}),
    ("api: CreateMessages", "POST", "/api/CreateMessages",
        {"meta_data": {"name": "X", "msg": "Hi"}}),

    # --- Users ---
    ("users: user (me)", "GET", "/users/user", None),
    ("users: UserProfileListView", "GET", "/users/UserProfileListView", None),
    ("users: StudentProfileListView", "GET", "/users/StudentProfileListView", None),
    ("users: InstructorProfileListView", "GET", "/users/InstructorProfileListView", None),
    ("users: dashboard-stats", "GET", "/users/dashboard-stats/", None),
    ("users: CreateUserProfile", "POST", "/users/CreateUserProfile",
        {"role": "Student", "phone_number": "+971500000000"}),

    # --- Courses: catalog & content ---
    ("courses: CourseListView", "GET", "/courses/CourseListView", None),
    ("courses: CategoryListView", "GET", "/courses/CategoryListView", None),
    ("courses: OrganizationListView", "GET", "/courses/OrganizationListView", None),
    ("courses: InstructorListView", "GET", "/courses/InstructorListView", None),
    ("courses: InstructorCourseListView", "GET", "/courses/InstructorCourseListView", None),
    ("courses: InstructorEnrollmentListView", "GET", "/courses/InstructorEnrollmentListView", None),
    ("courses: InstructorDiscussionListView", "GET", "/courses/InstructorDiscussionListView", None),
    ("courses: EnrolledCourseListView", "GET", "/courses/EnrolledCourseListView", None),
    ("courses: EnrollmentListView", "GET", "/courses/EnrollmentListView", None),
    ("courses: CourseAPIView(detail)", "GET", "/courses/1/CourseAPIView", None),
    ("courses: CategoryAPIView(detail)", "GET", "/courses/1/CategoryAPIView", None),
    ("courses: ModuleListView", "GET", "/courses/1/ModuleListView", None),
    ("courses: LessonListView", "GET", "/courses/1/LessonListView", None),
    ("courses: CourseResourceListView", "GET", "/courses/1/CourseResourceListView", None),
    ("courses: InstructorsAPIView", "GET", "/courses/1/InstructorsAPIView", None),
    ("courses: PresentationListView", "GET", "/courses/1/PresentationListView", None),
    ("courses: CheckEnrollment", "GET", "/courses/1/CheckEnrollment", None),
    ("courses: ModuleAPIView", "GET", "/courses/1/modules/1/ModuleAPIView", None),
    ("courses: LessonAPIView", "GET", "/courses/1/lessons/1/LessonAPIView", None),
    ("courses: CourseResourceAPIView", "GET", "/courses/1/resources/1/CourseResourceAPIView", None),

    # --- Courses: enrollment & progress ---
    ("courses: EnrollCourse", "POST", "/courses/EnrollCourse",
        {"course": 1}, ),

    # --- Reviews ---
    ("courses: reviews (list)", "GET", "/courses/1/reviews/", None),
    ("courses: instructor reviews", "GET", "/courses/instructor/reviews/", None),

    # --- Assessment ---
    ("courses: assessment (detail)", "GET", "/courses/1/assessment/", None),

    # --- Live sessions ---
    ("courses: live-sessions list", "GET", "/courses/live-sessions/", None),
    ("courses: live-sessions detail", "GET", "/courses/live-sessions/1/", None),
    ("courses: live-requests list", "GET", "/courses/live-requests/", None),

    # --- Booking & slots ---
    ("courses: availability list", "GET", "/courses/availability/", None),
    ("courses: slots list", "GET", "/courses/slots/", None),
    ("courses: bookings list", "GET", "/courses/bookings/", None),

    # --- Certificates ---
    ("courses: certificates", "GET", "/courses/certificates/", None),

    # --- Trainer & Student docs ---
    ("courses: trainer-documents", "GET", "/courses/trainer-documents/", None),
    ("courses: student-documents", "GET", "/courses/student-documents/", None),
    ("courses: instructor public (1)", "GET", "/courses/instructors/1/public/", None),
    ("courses: instructor verification (1)", "GET", "/courses/instructors/1/verification/", None),

    # --- Job roles ---
    ("courses: job-roles list", "GET", "/courses/job-roles/", None),
    ("courses: job-roles detail", "GET", "/courses/job-roles/1/", None),

    # --- Support ---
    ("courses: support channels", "GET", "/courses/support/channels/", None),
    ("courses: support tickets", "GET", "/courses/support/tickets/", None),
    ("courses: create support ticket", "POST", "/courses/support/tickets/",
        {"subject": "Help", "message": "Need assistance", "source": "web", "name": "Tester", "contact": "+971500000000"}),

    # --- Schedule ---
    ("courses: schedule", "GET", "/courses/schedule/", None),
]


def main():
    print(f"{'STATUS':6} {'METHOD':5} ENDPOINT")
    print("-" * 80)
    results = []
    for label, method, path, body in ENDPOINTS:
        code, body_preview = call(method, path, ADMIN_TOK, body)
        if code == 0:
            verdict = "ERROR"
        elif 200 <= code < 300:
            verdict = "OK"
        elif code == 401:
            verdict = "AUTH"
        elif code == 403:
            verdict = "FORBID"
        elif code == 404:
            verdict = "NOTFOUND"
        elif 400 <= code < 500:
            verdict = "CLIENT"
        else:
            verdict = "SERVER"
        results.append((label, method, path, code, verdict, body_preview))
        print(f"{code:>3} {verdict:6} {method:5} {path}")

    # Summary
    print()
    print("=" * 80)
    by_v = {}
    for _, _, _, _, v, _ in results:
        by_v[v] = by_v.get(v, 0) + 1
    print("SUMMARY:")
    for k in ("OK", "AUTH", "FORBID", "NOTFOUND", "CLIENT", "SERVER", "ERROR"):
        if k in by_v:
            print(f"  {k}: {by_v[k]}")
    print(f"TOTAL: {len(results)}")

    # Dump JSON for report
    with open("/tmp/sweep_results.json", "w") as f:
        json.dump([
            {"label": l, "method": m, "path": p, "code": c, "verdict": v, "body": b}
            for l, m, p, c, v, b in results
        ], f, indent=2)
    print("\nWrote /tmp/sweep_results.json")


if __name__ == "__main__":
    main()
