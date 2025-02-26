# Algebraic AI - 2025
# Go to github.com/Algebraic-AI for full license details.

import sys
import random
import networkx as nx
import matplotlib.pyplot as plt

import aml

# --------------------------------------------------------------------
# Configuration

# True: Obtain the freest model via the full crossing algorithm
#   It can be used for small graphs.
#   It becomes intractable for larger graphs
# False: Use the sparse crossing algorithm.
computeFullCrossing = False

# Save full crossing
saveAtomization = False
# Draw shortest cycle
drawFoundGraph = False

# If using sparse crossing:
#   Maximum number of iterations
maxAttempts = 10000
#   Learns to discard already found paths (hamiltonian or not) and subcycles.
combineWithTraining = True
#   Automatically adds edges to paths that can be trivially connected.
doCompletions = False

# Random seed for reproducibility
randseed = 12345

# Choose problem:
# 0: randomly connected cyclic graph
# 1: Petersen graph
# 2: Sheehan graph
problem = 1

aml.config.verbosityLevel = aml.config.Verbosity.Info

# -------------------------------------------------------------


def petersen_graph_adjacency(n: int, k: int) -> list[list[int]]:
    """
    Build the adjacency matrix the Petersen graph G(n, k).
    When n is congruent with 3 modulo 6, it has exactly 3 Hamiltonian cycles.
    Hard to find even for small sizes.
    Note that k must be less than n / 2, so the first such graph is G(9, 2).

    Ref: https://en.wikipedia.org/wiki/Generalized_Petersen_graph
    """

    # Best visualized drawn with the spectral layout `pos=nx.spectral_layout(G)`
    assert k < n / 2, "k must be less than n / 2"
    num_vertices = 2 * n
    adjacency_matrix = [[0] * num_vertices for _ in range(num_vertices)]

    for index in range(n):
        # first condition
        adjacency_matrix[index][(index + 1) % n] = 1
        adjacency_matrix[(index + 1) % n][index] = 1

        # second condition
        adjacency_matrix[index][index + n] = 1
        adjacency_matrix[index + n][index] = 1

        # third condition
        adjacency_matrix[n + index][n + ((index + k) % n)] = 1
        adjacency_matrix[n + ((index + k) % n)][n + index] = 1

    return adjacency_matrix


def sheehan_graph_adjacency(n: int) -> list[list[int]]:
    """
    Build the Sheehan graph H(n).
    H(n) is a graph with n vertices with exactly one hamiltonian cycle

    Ref: "Graphs with Exactly One Hamiltonian Circuit"
    https://doi.org/10.1002/jgt.3190010110
    """

    # Best visualized drawn with the circular layout `pos=nx.circular_layout(G)`
    num_vertices = n
    adjacency_matrix = [[0] * num_vertices for _ in range(num_vertices)]

    for index in range(num_vertices):
        adjacency_matrix[index][(index + 1) % n] = 1
        adjacency_matrix[(index + 1) % n][index] = 1

    for i in range(1, (n - 2) // 2 + 1):
        for j in range(2 * i + 1, n):
            adjacency_matrix[2 * i - 2][j - 1] = 1
            adjacency_matrix[j - 1][2 * i - 2] = 1

    return adjacency_matrix


# -------------------------------------------------------------


def printPath(atomization, embedding):
    """
    Prints edges and vertices in the current atomization
    """

    E = [{e} for e in embedding["EConstants"]]
    P = set(embedding["PConstants"])
    count = 0
    PathStr = "EDGES: "
    for e in range(0, nEdges):
        if aml.lowerOrEqual(aml.LCSegment(E[e]), aml.LCSegment(P), atomization):
            PathStr += f"{e}({EToVertexes[e]}), "
            count += 1

    PathStr += f"Total: {count}"

    print(PathStr)


def drawPath(atomization, embedding):
    """
    Draw the graph highlighting the edges that are in the path (P)
      according to the atomization.
    Make use of networkx and matplotlib libraries.
    """

    E = [{e} for e in embedding["EConstants"]]
    P = set(embedding["PConstants"])
    connected_edges = []
    for e in range(0, nEdges):
        if aml.lowerOrEqual(aml.LCSegment(E[e]), aml.LCSegment(P), atomization):
            connected_edges.append(EToVertexes[e])

    G = nx.Graph()
    G.add_edges_from(EToVertexes)
    val_map = {}
    values = [val_map.get(node, 0.25) for node in G.nodes()]
    edge_color = []
    for u, v, c in G.edges.data("color"):
        if [u, v] in connected_edges:
            edge_color.append("#ff0000")
        else:
            edge_color.append("#000000")
    nx.draw(
        G,
        # pos=nx.circular_layout(G),
        pos=nx.spring_layout(G, seed=10),
        cmap=plt.get_cmap("jet"),
        node_color=values,
        edge_color=edge_color,
    )
    plt.show()


def extractEdgesFromAtomization(atomization, embedding):
    """
    Returns, for each edge that according to the atomization is in the path (P),
      a tuple (a link) of the form [vertex1, vertex2, edge]
    """
    # nEdges, EToVertexes are global
    E = [{e} for e in embedding["EConstants"]]
    P = set(embedding["PConstants"])

    links = []
    for e in range(0, nEdges):
        if aml.lowerOrEqual(aml.LCSegment(E[e]), aml.LCSegment(P), atomization):
            lk = [EToVertexes[e][0], EToVertexes[e][1], e]
            links.append(lk)

    return links


def interpretPath(links):
    """
    Returns a list of "paths" from the input list "links".
    Each vertex is asumed to be in at most two links.
    Each "path" is returned as:
      [vertexes in the path, vertexes at the end of the path, set of connected links in the path]

    Vars:
       links: a list of tuples of the form [vertex1, vertex2, edge]
    """
    if len(links) == 0:
        return []
    if len(links) == 1:
        lk = links[0]
        vtx = set()
        vtx.add(lk[0])
        vtx.add(lk[1])
        extr = vtx.copy()
        path = [vtx, extr, [lk]]
        return [path]

    rLinks = links[1:]
    paths = interpretPath(rLinks)
    lk = links[0]

    ret = []
    connectedLeft = -1
    connectedRight = -1
    connectedCenter = -1
    i = 0
    for p in paths:
        vtx = p[0]
        extr = p[1]
        path = p[2]

        if lk[0] in extr and lk[1] in extr:
            extr = set()
            path.append(lk)
            ret.append([vtx, extr, path])
            connectedCenter = i
            i += 1
        elif lk[0] in extr:
            if connectedLeft > -1 or connectedCenter > -1:
                return []
            if connectedRight > -1:
                ret[connectedRight][0] |= vtx
                ret[connectedRight][1] |= extr
                ret[connectedRight][1].remove(lk[0])
                ret[connectedRight][2].extend(path)
            else:
                vtx.add(lk[1])
                extr.remove(lk[0])
                extr.add(lk[1])
                path.append(lk)
                connectedLeft = i
                ret.append([vtx, extr, path])
                i += 1
        elif lk[1] in extr:
            if connectedRight > -1 or connectedCenter > -1:
                return []
            if connectedLeft > -1:
                ret[connectedLeft][0] |= vtx
                ret[connectedLeft][1] |= extr
                ret[connectedLeft][1].remove(lk[1])
                ret[connectedLeft][2].extend(path)
            else:
                vtx.add(lk[0])
                extr.remove(lk[1])
                extr.add(lk[0])
                path.append(lk)
                connectedRight = i
                ret.append([vtx, extr, path])
                i += 1
        else:
            ret.append([vtx, extr, path])
            i += 1

    if connectedRight < 0 and connectedLeft < 0 and connectedCenter < 0:
        paths = interpretPath([lk])
        ret.extend(paths)

    return ret


def pathAnalysis(vertexesInGraph, links, doPathCompletion):
    """
    Each vertex of the graph is asumed to be in at most two links.
    Interprets the input list "links" as a list of paths.
       Each "path" is given by the tuple:
         [vertexes in the path, vertexes at the end of the path, set of connected links in the path]

    Returns:
       paths: the list of paths.
       vertexesInPaths: the set of all reached vertexes in all the paths.
       loops: number of closed paths.
       connected: True if there is a single path.
       hamiltonian: True if connected and reaching every vertex.
       completable: True if an edge can be trivially added.
       hasIsolatedVertexes: True if there are unconnected vertexes.
       pathkey: a unique identifier for the input set links.
       links: the input list links plus addtional links if doPathCompletion = True

    Vars:
       links: A set of tuples of the form [vertex1, vertex2, edge]
       vertexesInGraphv: The set of all the vertexes in the graph.
       doPathCompletion: Add edges to connect paths, if possible.
    """
    # nEdges, EToVertexes, VToNeighbours, nVertexes are globals

    links.sort(key=lambda lk: lk[2])
    paths = interpretPath(links)

    extrVertexes = set()
    for path in paths:
        extrVertexes |= path[1]

    vertexesInPaths = set([lk[0] for lk in links]) | set([lk[1] for lk in links])
    internalVertexes = vertexesInPaths - extrVertexes
    outsideEdgesList = list(
        set([e for e in range(0, nEdges)]) - set([lk[2] for lk in links])
    )

    if len(outsideEdgesList) + len(links) != nEdges:
        raise ValueError("error: outsideEdgesList + len(links) != nEdges")

    # make sure subpaths cannot be connected
    completable = False
    random.shuffle(outsideEdgesList)
    for e in outsideEdgesList:
        extr = set(EToVertexes[e])
        if extr & extrVertexes:
            if not extr & internalVertexes:
                closesPath = False
                for _, extrOfpath, _ in paths:
                    if len(extr & extrOfpath) == 2:
                        closesPath = True
                        break

                if len(paths) == 1 or not closesPath:
                    completable = True
                    if doPathCompletion:
                        print(f"This path has been completed with edge {e}")
                        lk = [EToVertexes[e][0], EToVertexes[e][1], e]
                        links.append(lk)
                        return pathAnalysis(vertexesInGraph, links, doPathCompletion)

    # has isolated vertexeses
    standigVertexes = vertexesInGraph - vertexesInPaths
    hasIsolatedVertexes = False
    for v in standigVertexes:
        if len(set(VToNeighbours[v]) & internalVertexes) == len(VToNeighbours[v]):
            hasIsolatedVertexes = True
            break

    if hasIsolatedVertexes and len(vertexesInPaths) == nVertexes:
        raise ValueError(
            "error: ", len(vertexesInPaths), len(vertexesInGraph), nVertexes
        )

    connected = len(paths) == 1
    loops = sum(1 for path in paths if len(path[1]) == 0)
    hamiltonian = (len(vertexesInPaths) == nVertexes) and connected
    pathkey = "-".join([str(lk[2]) for lk in links])

    return (
        paths,
        vertexesInPaths,
        loops,
        connected,
        hamiltonian,
        completable,
        hasIsolatedVertexes,
        pathkey,
        links,
    )


def interpret(atomization, doPathCompletion, embedding):
    # nEdges, EToVertexes are globals

    vertexesInGraph = set()
    for e in range(0, nEdges):
        vertexesInGraph |= set(EToVertexes[e])

    if nVertexes != len(vertexesInGraph):
        raise ValueError("error  nVertexes != len(vertexesInGraph)")

    links = extractEdgesFromAtomization(atomization, embedding)
    return pathAnalysis(vertexesInGraph, links, doPathCompletion)


def generateRandomlyConnectedCycleGraph(nVertextes, p, force):
    ady = [None] * nVertextes
    for v in range(0, nVertextes):
        ady[v] = [0] * nVertextes

    for v in range(0, nVertextes):
        connected = False
        while not connected:
            for vv in range(0, nVertextes):
                if v != vv:
                    if (random.random() < p) or (
                        force and (vv == v + 1 or (v == 0 and vv == nVertextes - 1))
                    ):
                        ady[v][vv] = 1
                        ady[vv][v] = 1
                    if ady[v][vv] == 1:
                        connected = True
    return ady


def showWithSortedPaths(links):
    """
    Prints the edges extracted from the input list "links" so
      consecutive edges share a vertex.
    Vars:
       links: A set of tuples of the form [vertex1, vertex2, edge]
    """
    sorted_edges = []
    visited_edges = list()
    visited_noedes = list()

    # Select an edge to start with
    start_edge = links[0]
    sorted_edges.append(start_edge)
    visited_edges.append(start_edge[2])
    node1 = start_edge[0]
    node2 = start_edge[1]
    visited_noedes.append(node1)
    visited_noedes.append(node2)

    while len(sorted_edges) < len(links):
        # Find the next edge that shares a node with the last edge in sorted_edges
        for edge in links:
            if edge[2] not in visited_edges and (edge[0] == node1 or edge[1] == node1):
                aux = [edge]
                aux.extend(sorted_edges)
                sorted_edges = aux
                visited_edges.append(edge[2])
                if edge[0] == node1:
                    node1 = edge[1]
                else:
                    node1 = edge[0]
                if node1 in visited_noedes:
                    if len(sorted_edges) < len(links):
                        print(node1)
                        raise ValueError("not hamiltonian")
                visited_noedes.append(node1)
                break

            if edge[2] not in visited_edges and (edge[0] == node2 or edge[1] == node2):
                sorted_edges.append(edge)
                visited_edges.append(edge[2])
                if edge[0] == node2:
                    node2 = edge[1]
                else:
                    node2 = edge[0]
                if node2 in visited_noedes:
                    if len(sorted_edges) < len(links):
                        print(node2)
                        raise ValueError("not hamiltonian")
                visited_noedes.append(node2)
                break

    print("In path order:")
    print(
        [str(e) + "([" + str(v1) + "," + str(v2) + "])" for v1, v2, e in sorted_edges]
    )


def getCycles(paths):
    """
    Extracts the cycles for the input list of paths,
      and for each cycle returns its list of edges.
    Vars:
       paths: a list of paths each of the form:
          [vertexes in the path, vertexes at the end of the path, set of connected links in the path]
          where each link has the form [vertex1, vertex2, edge]
    """
    ret = []
    for path in paths:
        if len(path[1]) == 0:
            links = path[2]
            edges = [eg[2] for eg in links]
            ret.append(edges)

    return ret


def getEdges(paths):
    """
    Returns, for each path, its list of edges.
    Vars:
       paths: a list of paths each of the form:
          [vertexes in the path, vertexes at the end of the path, set of connected links in the path]
          where each link has the form [vertex1, vertex2, edge]
    """
    ret = []
    for path in paths:
        links = path[2]
        edges = [eg[2] for eg in links]
        ret.extend(edges)

    return ret


def describePathExtensions(atomization, model, embedding):
    """
    Uses the atomization to obtain the set of edges that are in the path constant (P)
        and returns a list of duples, each duple with a right hand side term equal to
        the set of edges in P plus an additional edge not in P.
    The presence of these duples results in an increased probability of completing
        the curret path in the next batch.
    """
    E = [{e} for e in embedding["EConstants"]]
    P = set(embedding["PConstants"])
    WRONGPATH = set(embedding["WrongConstants"])

    edgSet = set()
    for e in range(0, nEdges):
        if aml.lowerOrEqual(aml.LCSegment(E[e]), aml.LCSegment(P), atomization):
            edgSet.add(e)

    term = P.copy()
    for e in edgSet:
        term |= E[e]

    auxn = []
    notTaken = set(e for e in range(0, nEdges)) - edgSet
    # Consider potential extensions of the current path
    for e in notTaken:
        # This duple may or may not be consistent with the embedding.
        rlt = aml.Duple(
            aml.LCSegment(WRONGPATH),
            aml.LCSegment(term | E[e]),
            False,
            model.generation,
            0,
        )
        # Hypotheses are enforced only if consistent
        rlt.hypothesis = True
        auxn.append(rlt)

    print("edgSet:", len(edgSet), "out:", len(notTaken))

    return auxn


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    random.seed(randseed)
    sys.setrecursionlimit(100000000)

    model = aml.Model()

    if problem == 0:
        nVertexes = 25
        ady = generateRandomlyConnectedCycleGraph(nVertexes, 0.075, True)
        graphname = f"{nVertexes} RANDOM"
    elif problem == 1:
        # When n is congruent with 3 modulo 6, it has exactly 3 Hamiltonian cycles.
        n = 9
        nVertexes = 2 * n
        ady = petersen_graph_adjacency(n, 2)
        graphname = " petersen " + str(nVertexes)
    elif problem == 2:
        # once the only Hamiltonian cycle is found,
        #   the embedding becomes inconsistent if combineWithTraining = True
        nVertexes = 30
        ady = sheehan_graph_adjacency(nVertexes)
        graphname = " sheehan " + str(nVertexes)
    else:
        raise IndexError("Problem index not found")

    print("vertexes", nVertexes)

    ex = 0
    EToVertexes = []
    VToNeighbours = [[] for v in range(0, nVertexes)]
    for v in range(0, nVertexes):
        for vv in range(0, v):
            if ady[v][vv] == 1:
                EToVertexes.append([vv, v])
                VToNeighbours[v].append(vv)
                VToNeighbours[vv].append(v)
                ex += 1
    nEdges = ex
    print("edges", nEdges)

    # Display graph
    G = nx.Graph()
    G.add_edges_from(EToVertexes)
    val_map = {}
    values = [val_map.get(node, 0.25) for node in G.nodes()]
    nx.draw(
        G,
        pos=nx.spring_layout(G, seed=10),
        cmap=plt.get_cmap("jet"),
        node_color=values,
        node_size=20,
    )
    plt.show()

    # --------------------------------------------------------------------
    # Load the embedding theory
    embedding = aml.amldl.load_embedding("embedding_HamiltonianCycles.py", ady)

    # Create constants
    constantNames = embedding["constantsNames"]
    for name in constantNames:
        # Add constants to the model's constant manager
        c = model.cmanager.setNewConstantIndexWithName(name)

        # Build the freest model: one atom for every constant
        at = aml.Atom(model.epoch, model.generation, [c])
        model.atomization.append(at)

    # Build duples
    p = embedding["positiveDuples"]
    n = embedding["negativeDuples"]

    # - build positive duples
    pduples = []
    for L, R, region, _ in p:
        rlt = aml.Duple(aml.LCSegment(L), aml.LCSegment(R), True, model.generation, region)  # fmt:skip
        pduples.append(rlt)

    # - build negative duples
    nduples = []
    for L, R, region, hyp in n:
        rlt = aml.Duple(aml.LCSegment(L), aml.LCSegment(R), False, model.generation, region)  # fmt:skip
        rlt.hypothesis = hyp
        nduples.append(rlt)

    # --------------------------------------------------------------------

    if computeFullCrossing:
        # Use full crossing
        # Only for very samll grpahs (fewer than 30 nodes)
        embedder = aml.full_crossing_embedder(model)
        embedder.params.sortDuples = True  # sorts the duples so the full crossing calculation is as fast as possible
        embedder.params.calculateRedundancy = True
        embedder.params.removeRepetitions = True

        embedder.enforce(pduples)

        if saveAtomization:
            aml.saveAtomizationOnFile(
                model.atomization,
                model.cmanager,
                "model_" + graphname,
            )
    else:
        # Use sparse crossing

        embedder = aml.sparse_crossing_embedder(model)

        reversedNameDictionary = model.cmanager.reversedNameDict

        embedder.params.storePositives = False
        embedder.params.byQuotient = False
        embedder.params.useReduceIndicators = True
        # smaller values than the default 1.5 may work better
        embedder.params.simplify_threshold = 1.1
        embedder.params.ignore_single_const_ucs = False
        # larger values than the default 0.1 may improve variability
        embedder.params.negativeIndicatorThreshold = 0.5

        initial = aml.atomizationCopy(model.atomization)

        pathDict = {}
        hamiltonianCycle_count = 0
        hamiltonianPath_count = 0
        subhamiltonian_count = 0

        rString = ""
        pathkey = ""
        lastpathkey = ""
        WP = model.cmanager.definedWithName["WRONGPATH"]
        CX = aml.CSegment(embedding["contextConstants"])
        attempt = 0
        while attempt < maxAttempts:
            print(
                f"           attempts: {attempt}",
                f" subhamiltonian: {subhamiltonian_count}",
                f" hamiltonian paths: {hamiltonianPath_count}",
                f" hamiltonian cycles: {hamiltonianCycle_count}",
                f" {graphname}",
                "------------------",
            )
            attempt += 1

            print("           unionModel:", len(embedder.unionModel), "\n")

            nduplesExt = nduples.copy()
            if lastpathkey == pathkey:
                # same path than the previus attempt
                # start from freest model
                embedder.setAtomization(aml.atomizationCopy(initial))
                # to avoid finding the same paths
                embedder.unionModel = [at for at in embedder.unionModel if not (WP in at.ucs)]  # fmt:skip
            else:
                # select a subset of atoms
                model.atomization, _, _ = aml.selectAtomsFromNegativeDuplesAndExplicit(
                    model.atomization, nduples, [], True, CX
                )
                # Keep the incomplete path of previous attempt and consider
                # potential extensions.
                nex = describePathExtensions(model.atomization, model, embedding)
                nduplesExt.extend(nex)

            embedder.enforce(pduples, nduplesExt)

            selection, _, inconsistent = aml.selectAtomsFromNegativeDuplesAndExplicit(
                model.atomization, nduples, [], True, CX
            )
            if inconsistent:
                print("Error: Inconsistent embedding")
                print("The embedding has some logical contradiction.")
                sys.exit(1)

            printPath(selection, embedding)

            lastpathkey = pathkey
            (
                paths,
                vertexesInPaths,
                loops,
                connected,
                hamiltonian,
                completable,
                hasIsolatedVertexes,
                pathkey,
                links,
            ) = interpret(selection, doCompletions, embedding)
            print(f"pieces: {len(paths)} loops {loops}")

            isnew = False
            if pathkey not in pathDict:
                pathDict[pathkey] = 0
                isnew = True
            pathDict[pathkey] += 1

            if isnew:
                print("New Path")
            else:
                print("Repeated Path")

            if hamiltonian:
                print("--- Hamiltonian!! -----")

                if isnew:
                    if loops == 1:
                        hamiltonianCycle_count += 1
                    else:
                        hamiltonianPath_count += 1

                    if drawFoundGraph:
                        showWithSortedPaths(links)
                        drawPath(selection, embedding)
                        aml.printLSpectrum(selection, None)

            if len(vertexesInPaths) == nVertexes and not hamiltonian:
                if isnew:
                    subhamiltonian_count += 1

            # report results
            if isnew:
                if hamiltonian and loops == 1:
                    rString += "O"
                elif hamiltonian:
                    rString += "H"
                else:
                    rString += "_"
            else:
                rString += " "
            print(rString)

            learnable = (
                ((len(vertexesInPaths) == nVertexes) and not completable)
                or hasIsolatedVertexes
                or loops > 0
            )

            # declare WRONGPATH the current path or its subcycles
            if learnable and combineWithTraining and isnew:
                E = [{e} for e in embedding["EConstants"]]
                P = set(embedding["PConstants"])
                WRONGPATH = set(embedding["WrongConstants"])

                if loops > 0:
                    loopPaths = getCycles(paths)
                    for loop in loopPaths:
                        term = set()
                        for e in loop:
                            term |= E[e]
                        rlt = aml.Duple(aml.LCSegment(WRONGPATH), aml.LCSegment(term), True, model.generation, 2)  # fmt:skip
                        pduples.append(rlt)

                else:
                    edges = getEdges(paths)
                    term = set()
                    for e in edges:
                        term |= E[e]
                    rlt = aml.Duple(aml.LCSegment(WRONGPATH), aml.LCSegment(term), True, model.generation, 2) # fmt:skip
                    pduples.append(rlt)
