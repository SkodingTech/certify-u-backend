"""
SCORM Package Service
Handles zip extraction, manifest parsing, and package structure creation
"""
import os
import json
import zipfile
import tempfile
import logging
from xml.etree import ElementTree as ET
from pathlib import Path
from urllib.parse import urljoin

from django.core.files.base import ContentFile
from django.conf import settings

from scorm.models import ScormPackage, ScormModule, ScormSco

logger = logging.getLogger(__name__)


class ScormPackageService:
    """Service for processing SCORM packages"""

    SCORM_NAMESPACES = {
        'imsmanifest': 'http://www.imsglobal.org/xsd/imscp_v1p1',
        'adlcp': 'http://www.adlnet.org/xsd/adlcp_v1p3',
        'adlseq': 'http://www.adlnet.org/xsd/adlseq_v1p3',
    }

    MAX_PACKAGE_SIZE = 500 * 1024 * 1024  # 500MB

    @classmethod
    def extract_and_parse(cls, package_id):
        """
        Extract SCORM zip and parse manifest
        Called by Celery task
        """
        try:
            package = ScormPackage.objects.get(id=package_id)

            # Extract zip
            with tempfile.TemporaryDirectory() as temp_dir:
                zip_path = package.upload_file.path
                cls._extract_zip(zip_path, temp_dir)

                # Find and parse manifest
                manifest_path = cls._find_manifest(temp_dir)
                if not manifest_path:
                    raise ValueError("imsmanifest.xml not found in package")

                # Parse manifest
                manifest_data = cls._parse_manifest(manifest_path)
                version = cls._detect_scorm_version(manifest_data)

                # Create package structure
                cls._create_package_structure(package, manifest_data, version, temp_dir)

                # Copy files to S3 (if using S3)
                cls._copy_package_files_to_storage(package, temp_dir)

                # Mark as ready
                package.mark_ready()
                logger.info(f"Package {package.id} processed successfully")

                return {
                    'success': True,
                    'package_id': package.id,
                    'version': version,
                    'total_scos': package.total_scos,
                    'total_modules': package.total_modules,
                }

        except Exception as e:
            logger.error(f"Error processing package {package_id}: {str(e)}")
            package.mark_error(str(e))
            return {
                'success': False,
                'package_id': package_id,
                'error': str(e),
            }

    @staticmethod
    def _extract_zip(zip_path, extract_to):
        """Extract SCORM zip file"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Check for zip bomb
                total_size = sum(zinfo.file_size for zinfo in zip_ref.infolist())
                if total_size > ScormPackageService.MAX_PACKAGE_SIZE:
                    raise ValueError("Package size exceeds maximum allowed")

                zip_ref.extractall(extract_to)
                logger.info(f"Extracted {len(zip_ref.namelist())} files")

        except zipfile.BadZipFile as e:
            raise ValueError(f"Invalid zip file: {str(e)}")

    @staticmethod
    def _find_manifest(directory):
        """Find imsmanifest.xml in extracted directory"""
        for root, dirs, files in os.walk(directory):
            if 'imsmanifest.xml' in files:
                return os.path.join(root, 'imsmanifest.xml')
        return None

    @classmethod
    def _parse_manifest(cls, manifest_path):
        """Parse imsmanifest.xml and return data"""
        tree = ET.parse(manifest_path)
        root = tree.getroot()

        # Extract namespace
        nsmap = cls._extract_namespaces(root.tag)

        manifest_data = {
            'identifier': root.get('identifier', 'unknown'),
            'version': root.get('version', ''),
            'organizations': cls._parse_organizations(root, nsmap),
            'resources': cls._parse_resources(root, nsmap),
            'metadata': cls._parse_metadata(root, nsmap),
        }

        return manifest_data

    @staticmethod
    def _extract_namespaces(tag):
        """Extract namespace from tag"""
        if '}' in tag:
            return tag.split('}')[0] + '}'
        return ''

    @classmethod
    def _parse_organizations(cls, root, ns):
        """Parse organizations from manifest"""
        orgs = []

        # Find organizations element
        orgs_elem = root.find(f'{ns}organizations')
        if orgs_elem is None:
            return orgs

        default_org = orgs_elem.get('default')

        for org in orgs_elem.findall(f'{ns}organization'):
            org_data = {
                'identifier': org.get('identifier', ''),
                'structure': org.get('structure', 'hierarchical'),
                'title': '',
                'items': [],
            }

            # Get title
            title_elem = org.find(f'{ns}title')
            if title_elem is not None and title_elem.text:
                org_data['title'] = title_elem.text

            # Parse items
            org_data['items'] = cls._parse_items(org, ns)
            orgs.append(org_data)

        return orgs

    @classmethod
    def _parse_items(cls, parent, ns, level=0):
        """Recursively parse items"""
        items = []

        for item in parent.findall(f'{ns}item'):
            item_data = {
                'identifier': item.get('identifier', ''),
                'identifierref': item.get('identifierref', ''),
                'parameters': item.get('parameters', ''),
                'title': '',
                'children': [],
                'level': level,
            }

            # Get title
            title_elem = item.find(f'{ns}title')
            if title_elem is not None and title_elem.text:
                item_data['title'] = title_elem.text

            # Recursive children
            item_data['children'] = cls._parse_items(item, ns, level + 1)
            items.append(item_data)

        return items

    @classmethod
    def _parse_resources(cls, root, ns):
        """Parse resources from manifest"""
        resources = {}

        resources_elem = root.find(f'{ns}resources')
        if resources_elem is None:
            return resources

        for resource in resources_elem.findall(f'{ns}resource'):
            resource_id = resource.get('identifier', '')
            resource_data = {
                'identifier': resource_id,
                'type': resource.get('type', ''),
                'href': resource.get('href', ''),
                'files': [],
                'scormType': resource.get('{http://www.adlnet.org/xsd/adlcp_v1p3}scormType', ''),
            }

            # Parse files
            for file_elem in resource.findall(f'{ns}file'):
                resource_data['files'].append({
                    'href': file_elem.get('href', ''),
                })

            resources[resource_id] = resource_data

        return resources

    @staticmethod
    def _parse_metadata(root, ns):
        """Parse metadata from manifest"""
        metadata = {
            'title': '',
            'description': '',
            'language': 'en',
        }

        metadata_elem = root.find(f'{ns}metadata')
        if metadata_elem is not None:
            schema = metadata_elem.find(f'{ns}schema')
            if schema is not None:
                metadata['schema'] = schema.text

            schema_version = metadata_elem.find(f'{ns}schemaversion')
            if schema_version is not None:
                metadata['schemaversion'] = schema_version.text

        return metadata

    @classmethod
    def _detect_scorm_version(cls, manifest_data):
        """Detect SCORM version from manifest"""
        # Check schemaversion
        schema_version = manifest_data.get('metadata', {}).get('schemaversion', '').lower()

        if '2004' in schema_version:
            return '2004'
        elif '1.2' in schema_version:
            return '1.2'

        # Check for 2004-specific namespace
        # This is a simple heuristic
        return 'unknown'

    @classmethod
    def _create_package_structure(cls, package, manifest_data, version, temp_dir):
        """Create ScormModule and ScormSco records"""
        package.version = version
        package.manifest_data = manifest_data

        # Get resources for easy lookup
        resources = manifest_data.get('resources', {})

        # Process first organization
        orgs = manifest_data.get('organizations', [])
        if orgs:
            org = orgs[0]

            # Find entry point from first item
            items = org.get('items', [])
            entry_point = cls._get_entry_point_from_items(items, resources, temp_dir)
            if entry_point:
                package.entry_point = entry_point

            # Create module hierarchy
            module_count = 0
            sco_count = 0

            for item in items:
                m_count, s_count = cls._create_item_structure(
                    package, None, item, resources, temp_dir, 0
                )
                module_count += m_count
                sco_count += s_count

            package.total_modules = module_count
            package.total_scos = sco_count

        package.structure_tree = manifest_data
        package.save()

    @classmethod
    def _get_entry_point_from_items(cls, items, resources, base_path):
        """Get launch URL from first item"""
        if not items:
            return None

        first_item = items[0]
        resource_id = first_item.get('identifierref')

        if resource_id and resource_id in resources:
            resource = resources[resource_id]
            href = resource.get('href')

            if href:
                # Check if file exists
                full_path = os.path.join(base_path, href)
                if os.path.exists(full_path):
                    return href

        # Try children
        children = first_item.get('children', [])
        if children:
            return cls._get_entry_point_from_items(children, resources, base_path)

        return None

    @classmethod
    def _create_item_structure(cls, package, parent_module, item, resources, base_path, order):
        """Recursively create module and SCO structure"""
        module_count = 0
        sco_count = 0

        item_id = item.get('identifier', '')
        item_title = item.get('title', item_id)
        resource_ref = item.get('identifierref', '')
        children = item.get('children', [])

        # Check if this is a branch (has children) or leaf (launchable)
        is_leaf = not children or (len(children) == 0)

        if is_leaf and resource_ref:
            # This is a SCO - launchable content
            resource = resources.get(resource_ref, {})
            launch_url = resource.get('href', '')

            if launch_url and os.path.exists(os.path.join(base_path, launch_url)):
                sco = ScormSco.objects.create(
                    package=package,
                    module=parent_module,
                    identifier=item_id,
                    title=item_title,
                    launch_url=launch_url,
                    resource_type=resource.get('type', 'webcontent'),
                    is_asset=resource.get('scormType', '').lower() == 'asset',
                    order=order,
                    visible=True,
                    required=False,
                )
                sco_count += 1
        else:
            # This is a module/folder
            module = ScormModule.objects.create(
                package=package,
                parent=parent_module,
                identifier=item_id,
                title=item_title,
                resource_ref=resource_ref,
                order=order,
                visible=True,
            )
            module_count += 1

            # Process children
            for child_order, child_item in enumerate(children):
                m_count, s_count = cls._create_item_structure(
                    package, module, child_item, resources, base_path, child_order
                )
                module_count += m_count
                sco_count += s_count

        return module_count, sco_count

    @staticmethod
    def _copy_package_files_to_storage(package, temp_dir):
        """
        Copy SCORM package files to storage (S3 if configured)
        For now, files are accessed directly from extracted zip
        """
        # Implementation depends on storage backend
        # If using S3, files should be uploaded here
        # For local storage, files can be left in extracted location
        pass


class ScormManifestValidator:
    """Validates SCORM manifest compliance"""

    @staticmethod
    def validate(manifest_data):
        """Validate manifest structure"""
        errors = []

        # Check required fields
        if not manifest_data.get('identifier'):
            errors.append("Missing manifest identifier")

        orgs = manifest_data.get('organizations', [])
        if not orgs:
            errors.append("No organizations found in manifest")

        if orgs:
            org = orgs[0]
            if not org.get('items'):
                errors.append("Organization has no items")

        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
        }
