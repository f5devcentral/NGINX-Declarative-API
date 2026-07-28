"""
Declaration parsing functions
"""

from typing import Dict, Any, List


def _patch_section_item(sourceDeclaration: dict, section_path: List[str], patched_item: dict) -> dict:
    """
    Generic helper to safely navigate a nested dictionary structure and patch/delete/add an item by name.

    Args:
        sourceDeclaration (dict): Source declaration dictionary to patch.
        section_path (List[str]): Path of keys to target section list (e.g. ['declaration', 'http', 'servers']).
        patched_item (dict): The item dictionary containing patch specifications.

    Returns:
        dict: The updated sourceDeclaration dictionary.
    """
    current = sourceDeclaration
    for i, key in enumerate(section_path[:-1]):
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]

    target_key = section_path[-1]
    if target_key not in current or not isinstance(current[target_key], list):
        current[target_key] = []

    all_target_items = []
    have_we_patched = False

    for s in current[target_key]:
        if s.get('name') == patched_item.get('name'):
            # Patching existing item. Item with only 'name' (len == 1) indicates deletion.
            if len(patched_item) > 1:
                all_target_items.append(patched_item)
            have_we_patched = True
        else:
            all_target_items.append(s)

    if not have_we_patched:
        # Item is new, append to target list
        all_target_items.append(patched_item)

    current[target_key] = all_target_items
    return sourceDeclaration


def patchHttpServer(sourceDeclaration: dict, patchedHttpServer: dict) -> dict:
    """
    Returns the patched declaration based on the patchedHttpServer.

    Args:
        sourceDeclaration (dict): Source declaration dictionary.
        patchedHttpServer (dict): HTTP server patch specifications.

    Returns:
        dict: Patched declaration dictionary.
    """
    return _patch_section_item(sourceDeclaration, ['declaration', 'http', 'servers'], patchedHttpServer)


def patchHttpUpstream(sourceDeclaration: dict, patchedHttpUpstream: dict) -> dict:
    """
    Returns the patched declaration based on the patchedHttpUpstream.

    Args:
        sourceDeclaration (dict): Source declaration dictionary.
        patchedHttpUpstream (dict): HTTP upstream patch specifications.

    Returns:
        dict: Patched declaration dictionary.
    """
    return _patch_section_item(sourceDeclaration, ['declaration', 'http', 'upstreams'], patchedHttpUpstream)


def patchStreamServer(sourceDeclaration: dict, patchedStreamServer: dict) -> dict:
    """
    Returns the patched declaration based on the patchedStreamServer.

    Args:
        sourceDeclaration (dict): Source declaration dictionary.
        patchedStreamServer (dict): Stream server patch specifications.

    Returns:
        dict: Patched declaration dictionary.
    """
    return _patch_section_item(sourceDeclaration, ['declaration', 'layer4', 'servers'], patchedStreamServer)


def patchStreamUpstream(sourceDeclaration: dict, patchedStreamUpstream: dict) -> dict:
    """
    Returns the patched declaration based on the patchedStreamUpstream.

    Args:
        sourceDeclaration (dict): Source declaration dictionary.
        patchedStreamUpstream (dict): Stream upstream patch specifications.

    Returns:
        dict: Patched declaration dictionary.
    """
    return _patch_section_item(sourceDeclaration, ['declaration', 'layer4', 'upstreams'], patchedStreamUpstream)


def patchNAPPolicies(sourceDeclaration: dict, patchedNAPPolicies: dict) -> dict:
    """
    Returns the patched declaration based on the patchedNAPPolicies.

    Args:
        sourceDeclaration (dict): Source declaration dictionary.
        patchedNAPPolicies (dict): NAP policies patch specifications.

    Returns:
        dict: Patched declaration dictionary.
    """
    if 'declaration' not in sourceDeclaration or \
       'http' not in sourceDeclaration['declaration'] or \
       'policies' not in sourceDeclaration['declaration']['http']:
        return sourceDeclaration

    allTargetPolicies = []
    haveWePatched = False

    for p in sourceDeclaration['declaration']['http']['policies']:
        if (p.get('type') == 'app_protect' and
                p.get('name') and
                p.get('type') == patchedNAPPolicies.get('type') and
                p.get('name') == patchedNAPPolicies.get('name')):

            if patchedNAPPolicies.get('versions') and patchedNAPPolicies.get('active_tag'):
                allTargetPolicies.append(patchedNAPPolicies)

            haveWePatched = True
        else:
            allTargetPolicies.append(p)

    if not haveWePatched:
        allTargetPolicies.append(patchedNAPPolicies)

    sourceDeclaration['declaration']['http']['policies'] = allTargetPolicies
    return sourceDeclaration


def patchCertificates(sourceDeclaration: dict, patchedCertificates: dict) -> dict:
    """
    Returns the patched declaration based on patchedCertificates.

    Args:
        sourceDeclaration (dict): Source declaration dictionary.
        patchedCertificates (dict): Certificates patch specifications.

    Returns:
        dict: Patched declaration dictionary.
    """
    if 'declaration' not in sourceDeclaration or \
       'http' not in sourceDeclaration['declaration'] or \
       'certificates' not in sourceDeclaration['declaration']['http']:
        return sourceDeclaration

    allTargetCertificates = []
    haveWePatched = False

    for c in sourceDeclaration['declaration']['http']['certificates']:
        if (c.get('type') in ['certificate', 'key'] and
                c.get('name') and
                c.get('type') == patchedCertificates.get('type') and
                c.get('name') == patchedCertificates.get('name')):

            if c.get('contents'):
                allTargetCertificates.append(patchedCertificates)

            haveWePatched = True
        else:
            allTargetCertificates.append(c)

    if not haveWePatched:
        allTargetCertificates.append(patchedCertificates)

    sourceDeclaration['declaration']['http']['certificates'] = allTargetCertificates
    return sourceDeclaration
