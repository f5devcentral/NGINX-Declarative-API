"""
Declaration parsing functions
"""

# Returns the patched declaration based on the patchedHttpServer
def patchHttpServer(sourceDeclaration: dict, patchedHttpServer: dict):
    allTargetServers = []

    haveWePatched = False

    if 'declaration' not in sourceDeclaration:
        sourceDeclaration['declaration'] = {}

    if 'http' not in sourceDeclaration['declaration']:
        sourceDeclaration['declaration']['http'] = {}

    if 'servers' not in sourceDeclaration['declaration']['http']:
        sourceDeclaration['declaration']['http']['servers'] = []

    # HTTP server patch
    for s in sourceDeclaration['declaration']['http']['servers']:
        if s['name'] == patchedHttpServer['name']:
            # Patching an existing HTTP server, 'name' is the key
            if len(patchedHttpServer) > 1:
                # Patching HTTP server specifying only 'name' (len == 1) means delete
                # If further fields are specified HTTP server is patched
                allTargetServers.append(patchedHttpServer)

            haveWePatched = True
        else:
            # Unmodified HTTP server
            allTargetServers.append(s)

    if not haveWePatched:
        # The HTTP server being patched is a new one, let's add it
        allTargetServers.append(patchedHttpServer)

    sourceDeclaration['declaration']['http']['servers'] = allTargetServers

    return sourceDeclaration


# Returns the patched declaration based on the patchedHttpUpstream
def patchHttpUpstream(sourceDeclaration: dict, patchedHttpUpstream: dict):
    allTargetUpstreams = []

    haveWePatched = False

    if 'declaration' not in sourceDeclaration:
        sourceDeclaration['declaration'] = {}

    if 'http' not in sourceDeclaration['declaration']:
        sourceDeclaration['declaration']['http'] = {}

    if 'upstreams' not in sourceDeclaration['declaration']['http']:
        sourceDeclaration['declaration']['http']['upstreams'] = []

    # HTTP upstreams patch
    for s in sourceDeclaration['declaration']['http']['upstreams']:
        if s['name'] == patchedHttpUpstream['name']:
            # Patching an existing HTTP upstream, 'name' is the key
            if len(patchedHttpUpstream) > 1:
                # Patching HTTP upstream specifying only 'name' (len == 1) means delete
                # If further fields are specified HTTP upstream is patched
                allTargetUpstreams.append(patchedHttpUpstream)

            haveWePatched = True
        else:
            # Unmodified HTTP upstream
            allTargetUpstreams.append(s)

    if not haveWePatched:
        # The HTTP upstream being patched is a new one, let's add it
        allTargetUpstreams.append(patchedHttpUpstream)

    sourceDeclaration['declaration']['http']['upstreams'] = allTargetUpstreams

    return sourceDeclaration

# Returns the patched declaration based on the patchedStreamServer
def patchStreamServer(sourceDeclaration: dict, patchedStreamServer: dict):
    allTargetServers = []

    haveWePatched = False

    if 'declaration' not in sourceDeclaration:
        sourceDeclaration['declaration'] = {}

    if 'layer4' not in sourceDeclaration['declaration']:
        sourceDeclaration['declaration']['layer4'] = {}

    if 'servers' not in sourceDeclaration['declaration']['layer4']:
        sourceDeclaration['declaration']['layer4']['servers'] = []

    # HTTP server patch
    for s in sourceDeclaration['declaration']['layer4']['servers']:
        if s['name'] == patchedStreamServer['name']:
            # Patching an existing Stream server, 'name' is the key
            if len(patchedStreamServer) > 1:
                # Patching Stream server specifying only 'name' (len == 1) means delete
                # If further fields are specified HTTP server is patched
                allTargetServers.append(patchedStreamServer)

            haveWePatched = True
        else:
            # Unmodified HTTP server
            allTargetServers.append(s)

    if not haveWePatched:
        # The Stream server being patched is a new one, let's add it
        allTargetServers.append(patchedStreamServer)

    sourceDeclaration['declaration']['layer4']['servers'] = allTargetServers

    return sourceDeclaration


# Returns the patched declaration based on the patchedStreamUpstream
def patchStreamUpstream(sourceDeclaration: dict, patchedStreamUpstream: dict):
    allTargetUpstreams = []

    haveWePatched = False

    if 'declaration' not in sourceDeclaration:
        sourceDeclaration['declaration'] = {}

    if 'layer4' not in sourceDeclaration['declaration']:
        sourceDeclaration['declaration']['layer4'] = {}

    if 'upstreams' not in sourceDeclaration['declaration']['layer4']:
        sourceDeclaration['declaration']['layer4']['upstreams'] = []

    # HTTP upstreams patch
    for s in sourceDeclaration['declaration']['layer4']['upstreams']:
        if s['name'] == patchedStreamUpstream['name']:
            # Patching an existing Stream upstream, 'name' is the key
            if len(patchedStreamUpstream) > 1:
                # Patching Stream upstream specifying only 'name' (len == 1) means delete
                # If further fields are specified HTTP upstream is patched
                allTargetUpstreams.append(patchedStreamUpstream)

            haveWePatched = True
        else:
            # Unmodified HTTP upstream
            allTargetUpstreams.append(s)

    if not haveWePatched:
        # The Stream upstream being patched is a new one, let's add it
        allTargetUpstreams.append(patchedStreamUpstream)

    sourceDeclaration['declaration']['layer4']['upstreams'] = allTargetUpstreams

    return sourceDeclaration
