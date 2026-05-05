"""
Celery Tasks for SCORM Module
Handles async processing like zip extraction and package parsing
"""
import logging
from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

from scorm.models import ScormPackage
from scorm.services import ScormPackageService, ScormManifestValidator

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def extract_and_parse_scorm_package(self, package_id):
    """
    Extract and parse SCORM package asynchronously
    Triggered when user uploads a SCORM zip file
    """
    try:
        logger.info(f"Starting extraction for package {package_id}")

        # Process package
        result = ScormPackageService.extract_and_parse(package_id)

        if result['success']:
            # Send success notification
            send_scorm_package_ready_email(package_id)
            logger.info(f"Package {package_id} processed successfully")
        else:
            logger.error(f"Package {package_id} processing failed: {result['error']}")

        return result

    except Exception as exc:
        logger.error(f"Error in extract_and_parse_scorm_package: {str(exc)}")

        # Retry with exponential backoff
        try:
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        except self.MaxRetriesExceededError:
            package = ScormPackage.objects.get(id=package_id)
            package.mark_error(f"Processing failed after {self.max_retries} retries")
            logger.critical(f"Max retries exceeded for package {package_id}")


@shared_task
def send_scorm_package_ready_email(package_id):
    """
    Send email notification when SCORM package is ready
    """
    try:
        package = ScormPackage.objects.get(id=package_id)

        # Get package creator (admin who uploaded)
        # Assuming creator is stored in metadata or we use first admin
        admins = [admin for admin in [settings.ADMINS] if admin]

        if not admins:
            logger.warning(f"No admin email configured for package {package_id}")
            return

        subject = f"SCORM Package Ready: {package.title}"
        context = {
            'package_title': package.title,
            'package_id': package.id,
            'version': package.version,
            'total_scos': package.total_scos,
            'total_modules': package.total_modules,
            'dashboard_url': f"{settings.SITE_URL}/dashboard/scorm/view",
        }

        html_message = render_to_string(
            'scorm/email/package_ready.html',
            context
        )

        # Send to all admins
        admin_emails = [admin[1] for admin in admins]

        send_mail(
            subject,
            f"SCORM package '{package.title}' has been processed and is ready for use.",
            settings.DEFAULT_FROM_EMAIL,
            admin_emails,
            html_message=html_message,
            fail_silently=True,
        )

        logger.info(f"Ready email sent for package {package_id}")

    except ScormPackage.DoesNotExist:
        logger.error(f"Package {package_id} not found for email notification")
    except Exception as e:
        logger.error(f"Error sending package ready email: {str(e)}")


@shared_task
def archive_old_scorm_sessions():
    """
    Archive old SCORM session data (>6 months)
    Keeps database clean and optimizes queries
    Called periodically (weekly or monthly)
    """
    from datetime import timedelta
    from django.utils import timezone

    try:
        cutoff_date = timezone.now() - timedelta(days=180)

        from scorm.models import ScormTracking

        old_sessions = ScormTracking.objects.filter(
            last_access__lt=cutoff_date,
            is_deleted=False
        ).update(is_deleted=True)

        logger.info(f"Archived {old_sessions} old SCORM sessions")

        return {
            'success': True,
            'archived_count': old_sessions,
        }

    except Exception as e:
        logger.error(f"Error archiving SCORM sessions: {str(e)}")
        return {
            'success': False,
            'error': str(e),
        }


@shared_task
def calculate_scorm_completion_statistics():
    """
    Calculate completion statistics for all SCORM packages
    Stored for dashboard analytics
    Called periodically
    """
    try:
        from scorm.models import ScormTracking, ScormPackage

        for package in ScormPackage.objects.filter(is_active=True, is_deleted=False):
            total_users = ScormTracking.objects.filter(
                package=package
            ).values('user').distinct().count()

            completed_users = ScormTracking.objects.filter(
                package=package,
                lesson_status__in=['completed', 'passed']
            ).values('user').distinct().count()

            avg_score = ScormTracking.objects.filter(
                package=package,
                score_raw__isnull=False
            ).values('score_raw').aggregate(
                avg=models.Avg('score_raw')
            )

            # Store in metadata
            if not isinstance(package.manifest_data, dict):
                package.manifest_data = {}

            package.manifest_data['statistics'] = {
                'total_enrolled': total_users,
                'total_completed': completed_users,
                'completion_rate': round((completed_users / total_users * 100), 2) if total_users > 0 else 0,
                'average_score': round(avg_score.get('avg', 0) or 0, 2),
                'last_calculated': timezone.now().isoformat(),
            }

            package.save()

        logger.info("SCORM completion statistics calculated")

        return {
            'success': True,
            'packages_updated': ScormPackage.objects.filter(
                is_active=True, is_deleted=False
            ).count(),
        }

    except Exception as e:
        logger.error(f"Error calculating SCORM statistics: {str(e)}")
        return {
            'success': False,
            'error': str(e),
        }
