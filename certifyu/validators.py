"""Reusable upload validators.

Use as `validators=[ValidateFileType(IMAGE_TYPES)]` on a FileField/ImageField.
Stronger than relying on filename — sniffs the first bytes for magic numbers.
"""
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible


IMAGE_TYPES   = {'image/png', 'image/jpeg', 'image/webp', 'image/gif'}
DOC_TYPES     = {'application/pdf'}
VIDEO_TYPES   = {'video/mp4', 'video/webm'}
SCORM_TYPES   = {'application/zip', 'application/x-zip-compressed'}
ALL_UPLOAD_TYPES = IMAGE_TYPES | DOC_TYPES | VIDEO_TYPES | SCORM_TYPES


# Magic-byte sniffer (covers the cases the Django UploadedFile content_type
# header can be spoofed — checks the first bytes against known signatures).
_MAGIC = [
    (b'\x89PNG\r\n\x1a\n',           'image/png'),
    (b'\xff\xd8\xff',                'image/jpeg'),
    (b'GIF87a',                      'image/gif'),
    (b'GIF89a',                      'image/gif'),
    (b'RIFF',                        'image/webp'),     # also audio/wav; rely on extension for further check
    (b'%PDF-',                       'application/pdf'),
    (b'PK\x03\x04',                  'application/zip'),
    (b'\x00\x00\x00\x18ftypmp4',     'video/mp4'),
    (b'\x00\x00\x00\x20ftypiso',     'video/mp4'),
    (b'\x1aE\xdf\xa3',               'video/webm'),
]


def _sniff(fileobj):
    pos = fileobj.tell()
    head = fileobj.read(16)
    fileobj.seek(pos)
    for sig, mime in _MAGIC:
        if head.startswith(sig):
            return mime
    return None


@deconstructible
class ValidateFileType:
    """Reject uploads whose declared content_type isn't in `allowed`, AND whose
    sniffed magic bytes don't match. Both signals must agree."""

    def __init__(self, allowed, max_size_mb=25):
        self.allowed = set(allowed)
        self.max_size_mb = max_size_mb

    def __call__(self, file):
        if file.size and file.size > self.max_size_mb * 1024 * 1024:
            raise ValidationError(
                f'File is too large ({file.size // (1024*1024)} MB); '
                f'maximum is {self.max_size_mb} MB.'
            )
        declared = getattr(file, 'content_type', '') or ''
        if declared and declared not in self.allowed:
            raise ValidationError(
                f'File type {declared!r} not permitted. '
                f'Allowed: {sorted(self.allowed)}.'
            )
        sniffed = _sniff(file)
        if sniffed is not None and sniffed not in self.allowed:
            raise ValidationError(
                f'File contents look like {sniffed!r}, which is not permitted.'
            )

    def __eq__(self, other):
        return (isinstance(other, ValidateFileType)
                and self.allowed == other.allowed
                and self.max_size_mb == other.max_size_mb)

    def __hash__(self):
        return hash((frozenset(self.allowed), self.max_size_mb))
