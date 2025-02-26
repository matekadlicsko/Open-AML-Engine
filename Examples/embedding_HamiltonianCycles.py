# Algebraic AI - 2025
# Go to github.com/Algebraic-AI for full license details.

from aml.amldl import (
    ADD,
    APP,
    C,
    CV,
    CMP,
    Descriptor,
    EXC,
    F,
    HEADER,
    INC,
    M,
    R,
    SOME,
    T,
    V,
    S,
)

_i = 1


def embedding(ady):

    useZ = True
    useLoopId = True
    nodeImpliesId = True

    if nodeImpliesId and not useLoopId:
        raise ValueError()

    nVertexes = len(ady)
    VToEdges = [None]*nVertexes
    for v in range(0, nVertexes):
        VToEdges[v] = []

    ex = 0
    for v in range(0, nVertexes):
        for vv in range(0, v):
            if ady[v][vv] ==  1:
                VToEdges[v].append(ex)
                VToEdges[vv].append(ex)
                ex += 1
    nEdges = ex

    DESC = Descriptor()
    with DESC as theEmbedding:
        if HEADER("graph embedding"):
            CV("V", nVertexes)
            if useLoopId:
                CV("id", nVertexes)
            CV("E", nEdges)
            CV("nE", nEdges)
            if useZ:
                CV("Z", nEdges)
            CV("g", nEdges)
            CV("h", nEdges)
            C("P")
            C("WRONGPATH")

        Qvars = M("V", "E", "P")
        CX = M("g", "h")


        theEmbedding.REGION = 1

        # Graph topology
        ex = 0
        for v in range(0, nVertexes):
            for vv in range(0, v):
                if ady[v][vv] ==  1:
                    ADD(INC(
                            M(F("V", v), F("V", vv)),
                            F("E", ex)
                    ))
                    ex += 1

        # Vertexes can only be obtained from edges (optional)
        for v in range(0, nVertexes):
            edges = VToEdges[v]
            term = R("V", F("V", v))
            term = M(term, "nE")
            if useLoopId and not nodeImpliesId:
                term = R("id", F("id", v))
            for e in range(0, nEdges):
                if not e in set(edges):
                    term = M(term, F("E", e))

            if useLoopId:
                ADD(EXC(F("id", v), term))

            if not (useLoopId and nodeImpliesId):
                ADD(EXC(F("V", v), term))

        # Transfer the same ID along the vertexes of a connected path
        if useLoopId:
            ex = 0
            for v in range(0, nVertexes):
                if nodeImpliesId:
                    ADD(INC(F("id", v), F("V", v)))
                for vv in range(0, v):
                    if ady[v][vv] ==  1:
                        ADD(INC(F("id", v), M(F("id", vv), F("E", ex))))
                        ADD(INC(F("id", vv), M(F("id", v), F("E", ex))))
                        ex += 1
            for v in range(0, nVertexes):
                for vv in range(0, v):
                    ADD(INC(F("id", v), M(F("id", vv), "P")))
                    ADD(INC(F("id", vv), M(F("id", v), "P")))

        ADD(INC("V", "P"))

        if useZ:
            ADD(INC(T("Z", _i), M(T("E", _i), T("nE", _i))))
            ADD(INC("Z", "P"))
            ADD(INC("P", "Z"))
        else:
            ADD(INC("P", M("E", "nE")))

        ADD(EXC("WRONGPATH", "P"))


        # Two edges of the same vertex imply the other edges of the vertex are out
        for v in range(0, nVertexes):
            edges = VToEdges[v]
            if len(edges) == 2:
                ledges = list(edges)
                if useZ:
                    ADD(INC(F("E", ledges[0]), F("Z", ledges[0])))
                    ADD(INC(F("Z", ledges[0]), F("E", ledges[0])))
                    ADD(INC(F("E", ledges[1]), F("Z", ledges[1])))
                    ADD(INC(F("Z", ledges[1]), F("E", ledges[1])))
                else:
                    ADD(INC(F("E", ledges[0]), "P"))
                    ADD(INC(F("E", ledges[1]), "P"))
            elif len(edges) == 1:
                raise ValueError("This node with one edge cannot be part of a cycle")
            for e1 in edges:
                for e2 in edges:
                    if e2 > e1:
                        term = None
                        for e3 in edges:
                            if e3 != e1 and e3 != e2:
                                if term is None:
                                    term = F("nE", e3)
                                else:
                                    term = M(term, F("nE", e3))

                        if term is None:
                            continue

                        ADD(INC(
                            term,
                            M(F("E", e1), F("E", e2), "P")
                        ))

                        ADD(INC(
                            M(F("E", e1), F("E", e2)),
                            M(term, "P")
                        ))

        # do not take edge and empty at the same time
        for e in range(0, nEdges):
            ADD(INC(
                    "WRONGPATH",
                    M(F("E", e), F("nE", e), "P")
            ))

        # Make the embedding explicit
        if True:
            for e in range(0, nEdges):
                if useZ:
                    ADD(INC(F("E", e), M(F("Z", e), F("g", e))))
                    ADD(INC(F("Z", e), M(F("E", e), F("g", e))))

                    ADD(INC(F("nE", e), M(F("Z", e), F("h", e))))
                    ADD(INC(F("Z", e), M(F("nE", e), F("h", e))))
                else:
                    ADD(INC(F("E", e), M("P", F("g", e))))
                    ADD(INC(F("nE", e), M("P", F("h", e))))

        if False:
            ## ---------------------
            print("Constants")
            print([el.const for el in F("constants pending transfer to algebra").r])
            print("Inclusions")
            for el in F("inclusions").r:
                print(el.rl_L.s, el.rl_H.s)
            print("Exclusions")
            for el in F("exclusions").r:
                print(el.rl_L.s, el.rl_H.s)
            ## ---------------------

        # return DESC, CX, Qvars
        return {
            "descriptor": DESC,
            "constants": [el.const for el in F("constants pending transfer to algebra").r],  # fmt:skip
            "constantsNames": [el.key for el in F("constants pending transfer to algebra").r],  # fmt:skip
            "positiveDuples": [(el.rl_L.s, el.rl_H.s, el.region, el.treatAsHypothesis) for el in F("inclusions").r],  # fmt:skip
            "negativeDuples": [(el.rl_L.s, el.rl_H.s, el.region, el.treatAsHypothesis) for el in F("exclusions").r],  # fmt:skip
            "contextConstants": S(CX).s,
            "PConstants": S(F("P")).s,
            "WrongConstants": S(F("WRONGPATH")).s,
            "EConstants": [el.const for el in F("E").v],
            "nEConstants": [el.const for el in F("nE").v],
            }
