"""
SCORM Runtime Engine
Handles CMI state machine, GetValue/SetValue operations, and API calls
Implements both SCORM 1.2 and SCORM 2004 specifications
"""
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from scorm.models import ScormTracking, ScormRuntimeData

logger = logging.getLogger(__name__)


class ScormRuntimeEngine:
    """
    Handles SCORM runtime CMI processing
    Manages GetValue, SetValue, and Commit operations
    """

    # SCORM 1.2 CMI Elements
    CMI_ELEMENTS_1_2 = {
        'cmi.core.student_id': {'type': 'string', 'readable': True, 'writable': False},
        'cmi.core.student_name': {'type': 'string', 'readable': True, 'writable': False},
        'cmi.core.lesson_location': {'type': 'string', 'readable': True, 'writable': True},
        'cmi.core.lesson_status': {'type': 'string', 'readable': True, 'writable': True},
        'cmi.core.score.raw': {'type': 'integer', 'readable': True, 'writable': True},
        'cmi.core.score.max': {'type': 'integer', 'readable': True, 'writable': False},
        'cmi.core.score.min': {'type': 'integer', 'readable': True, 'writable': False},
        'cmi.core.time_spent': {'type': 'string', 'readable': True, 'writable': False},
        'cmi.suspend_data': {'type': 'string', 'readable': True, 'writable': True},
        'cmi.comments': {'type': 'string', 'readable': True, 'writable': True},
        'cmi.entry': {'type': 'string', 'readable': True, 'writable': False},
        'cmi.exit': {'type': 'string', 'readable': True, 'writable': True},
        'cmi.objectives._count': {'type': 'integer', 'readable': True, 'writable': False},
        'cmi.interactions._count': {'type': 'integer', 'readable': True, 'writable': False},
    }

    # SCORM 2004 CMI Elements
    CMI_ELEMENTS_2004 = {
        'cmi.learner_id': {'type': 'string', 'readable': True, 'writable': False},
        'cmi.learner_name': {'type': 'string', 'readable': True, 'writable': False},
        'cmi.location': {'type': 'string', 'readable': True, 'writable': True},
        'cmi.completion_status': {'type': 'string', 'readable': True, 'writable': True},
        'cmi.progress_measure': {'type': 'decimal', 'readable': True, 'writable': True},
        'cmi.score.raw': {'type': 'decimal', 'readable': True, 'writable': True},
        'cmi.score.scaled': {'type': 'decimal', 'readable': True, 'writable': True},
        'cmi.score.min': {'type': 'decimal', 'readable': True, 'writable': False},
        'cmi.score.max': {'type': 'decimal', 'readable': True, 'writable': False},
        'cmi.success_status': {'type': 'string', 'readable': True, 'writable': True},
        'cmi.suspend_data': {'type': 'string', 'readable': True, 'writable': True},
        'cmi.exit': {'type': 'string', 'readable': True, 'writable': True},
        'cmi.total_time': {'type': 'string', 'readable': True, 'writable': False},
    }

    # SCORM Lesson Status Values
    LESSON_STATUS_VALUES = ['passed', 'completed', 'failed', 'incomplete', 'browsed', 'not attempted']

    # Error Codes
    ERROR_CODES = {
        '0': 'No error',
        '101': 'General Exception',
        '201': 'Invalid argument',
        '202': 'Element cannot have children',
        '203': 'Element not an array',
        '301': 'Not initialized',
        '401': 'Not implemented',
        '402': 'Invalid set value',
        '403': 'Element is read-only',
        '404': 'Element is write-only',
        '405': 'Incorrect data type',
    }

    def __init__(self, scorm_version='1.2'):
        """Initialize runtime engine with SCORM version"""
        self.version = scorm_version
        self.cmi_elements = self.CMI_ELEMENTS_1_2 if scorm_version == '1.2' else self.CMI_ELEMENTS_2004
        self.last_error = '0'

    def initialize(self, tracking):
        """
        Initialize SCORM session
        SCORM API: Initialize()
        """
        try:
            # Set entry status
            if tracking.entry_status == 'ab-initio':
                # Fresh start - initialize CMI data
                self._init_cmi_data(tracking)
            else:
                # Resume - restore suspend_data
                pass

            return {
                'success': True,
                'error_code': '0',
                'message': 'Initialized',
            }

        except Exception as e:
            logger.error(f"Initialize error: {str(e)}")
            self.last_error = '101'
            return {
                'success': False,
                'error_code': '101',
                'message': str(e),
            }

    def get_value(self, tracking, element):
        """
        Get CMI element value
        SCORM API: GetValue(element)
        """
        try:
            # Validate element
            if element not in self.cmi_elements:
                self.last_error = '201'
                return {
                    'value': '',
                    'error_code': '201',
            }

            element_spec = self.cmi_elements[element]

            # Check if readable
            if not element_spec.get('readable'):
                self.last_error = '404'
                return {
                    'value': '',
                    'error_code': '404',
                }

            # Get value from runtime data
            value = ScormRuntimeData.get_value(tracking, element)

            if value is None:
                # Return default value
                value = self._get_default_value(element)

            self.last_error = '0'
            return {
                'value': str(value) if value is not None else '',
                'error_code': '0',
            }

        except Exception as e:
            logger.error(f"GetValue error: {str(e)}")
            self.last_error = '101'
            return {
                'value': '',
                'error_code': '101',
            }

    def set_value(self, tracking, element, value):
        """
        Set CMI element value
        SCORM API: SetValue(element, value)
        """
        try:
            # Validate element
            if element not in self.cmi_elements:
                self.last_error = '201'
                return {
                    'error_code': '201',
                    'message': 'Invalid argument',
                }

            element_spec = self.cmi_elements[element]

            # Check if writable
            if not element_spec.get('writable'):
                self.last_error = '403'
                return {
                    'error_code': '403',
                    'message': 'Element is read-only',
                }

            # Validate data type
            validation = self._validate_value(element, value, element_spec)
            if not validation['valid']:
                self.last_error = '405'
                return {
                    'error_code': '405',
                    'message': validation['message'],
                }

            # Store value
            ScormRuntimeData.set_value(tracking, element, value)

            # Update tracking based on special elements
            self._update_tracking_from_cmi(tracking, element, value)

            self.last_error = '0'
            return {
                'error_code': '0',
                'message': 'Value set',
            }

        except Exception as e:
            logger.error(f"SetValue error: {str(e)}")
            self.last_error = '101'
            return {
                'error_code': '101',
                'message': str(e),
            }

    def commit(self, tracking):
        """
        Commit (persist) CMI data
        SCORM API: Commit("")
        """
        try:
            with transaction.atomic():
                # Mark all runtime data as committed
                for runtime_data in ScormRuntimeData.objects.filter(tracking=tracking):
                    runtime_data.commit_count += 1
                    runtime_data.save()

                # Calculate aggregate data
                self._update_tracking_aggregates(tracking)

                tracking.save()

            self.last_error = '0'
            return {
                'error_code': '0',
                'message': 'Data committed',
            }

        except Exception as e:
            logger.error(f"Commit error: {str(e)}")
            self.last_error = '101'
            return {
                'error_code': '101',
                'message': str(e),
            }

    def finish(self, tracking):
        """
        Finish SCORM session
        SCORM API: Finish("")
        """
        try:
            # Final commit
            self.commit(tracking)

            # Update completion
            with transaction.atomic():
                lesson_status = ScormRuntimeData.get_value(
                    tracking,
                    'cmi.core.lesson_status' if self.version == '1.2' else 'cmi.completion_status'
                )

                if lesson_status in ['completed', 'passed']:
                    tracking.lesson_status = lesson_status
                    tracking.completion_date = timezone.now()

                # Get final score
                score_elem = 'cmi.core.score.raw' if self.version == '1.2' else 'cmi.score.raw'
                score = ScormRuntimeData.get_value(tracking, score_elem)
                if score:
                    try:
                        tracking.score_raw = int(float(score))
                    except (ValueError, TypeError):
                        pass

                tracking.save()

            self.last_error = '0'
            return {
                'error_code': '0',
                'message': 'Session finished',
            }

        except Exception as e:
            logger.error(f"Finish error: {str(e)}")
            self.last_error = '101'
            return {
                'error_code': '101',
                'message': str(e),
            }

    def get_last_error(self):
        """Return last error code"""
        return self.last_error

    def get_error_string(self, error_code):
        """Get error message for error code"""
        return self.ERROR_CODES.get(error_code, 'Unknown error')

    # Private helper methods

    def _init_cmi_data(self, tracking):
        """Initialize default CMI data"""
        if self.version == '1.2':
            ScormRuntimeData.set_value(tracking, 'cmi.core.student_id', str(tracking.user.id))
            ScormRuntimeData.set_value(tracking, 'cmi.core.student_name', tracking.user.get_full_name() or tracking.user.username)
            ScormRuntimeData.set_value(tracking, 'cmi.core.lesson_status', 'not attempted')
            ScormRuntimeData.set_value(tracking, 'cmi.core.score.raw', '0')
            ScormRuntimeData.set_value(tracking, 'cmi.core.score.max', str(tracking.package.scos.count() * 100))
            ScormRuntimeData.set_value(tracking, 'cmi.entry', 'ab-initio')
        else:
            ScormRuntimeData.set_value(tracking, 'cmi.learner_id', str(tracking.user.id))
            ScormRuntimeData.set_value(tracking, 'cmi.learner_name', tracking.user.get_full_name() or tracking.user.username)
            ScormRuntimeData.set_value(tracking, 'cmi.completion_status', 'not completed')
            ScormRuntimeData.set_value(tracking, 'cmi.score.raw', '0')
            ScormRuntimeData.set_value(tracking, 'cmi.score.max', str(tracking.package.scos.count() * 100))

    def _get_default_value(self, element):
        """Get default value for CMI element"""
        defaults = {
            'cmi.core.lesson_status': 'not attempted',
            'cmi.completion_status': 'not completed',
            'cmi.core.score.raw': '0',
            'cmi.score.raw': '0',
            'cmi.suspend_data': '',
            'cmi.entry': 'ab-initio',
        }
        return defaults.get(element, '')

    def _validate_value(self, element, value, element_spec):
        """Validate CMI value against type"""
        elem_type = element_spec.get('type', 'string')

        try:
            if elem_type == 'string':
                return {'valid': True}
            elif elem_type == 'integer':
                int(value)
                return {'valid': True}
            elif elem_type == 'decimal':
                float(value)
                return {'valid': True}
            else:
                return {'valid': True}
        except (ValueError, TypeError):
            return {
                'valid': False,
                'message': f'Invalid {elem_type} value: {value}',
            }

    def _update_tracking_from_cmi(self, tracking, element, value):
        """Update tracking record based on CMI element changes"""
        # Map important CMI changes to tracking fields
        if element in ['cmi.core.lesson_status', 'cmi.completion_status']:
            if value in self.LESSON_STATUS_VALUES:
                tracking.lesson_status = value

        elif element in ['cmi.core.score.raw', 'cmi.score.raw']:
            try:
                tracking.score_raw = int(float(value))
            except (ValueError, TypeError):
                pass

        elif element in ['cmi.core.lesson_location', 'cmi.location']:
            tracking.bookmark = value

        elif element == 'cmi.suspend_data':
            tracking.suspend_data = value

    def _update_tracking_aggregates(self, tracking):
        """Update aggregate tracking fields"""
        # Get final score
        score_elem = 'cmi.core.score.raw' if self.version == '1.2' else 'cmi.score.raw'
        score = ScormRuntimeData.get_value(tracking, score_elem)

        if score:
            try:
                raw_score = int(float(score))
                tracking.score_raw = raw_score

                # Calculate scaled score
                if tracking.score_max > 0:
                    tracking.score_scaled = raw_score / tracking.score_max
            except (ValueError, TypeError):
                pass
