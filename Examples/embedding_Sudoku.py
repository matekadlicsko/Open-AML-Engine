# Algebraic AI - 2025
# Go to github.com/Algebraic-AI for full license details.

from aml.amldl import (
    ADD,
    C,
    CV,
    CMP,
    Descriptor,
    EXC,
    F,
    HEADER,
    INC,
    M,
    T,
    S,
)

_i = 1

# learn with poisitve duples that a grid is inconsistent
usePositives = True


def embedding(gridDimension):

    if gridDimension == 4:
        numberOfSubgrids = 4

        zMap = [
            [0, 0, 1, 1],
            [0, 0, 1, 1],
            [2, 2, 3, 3],
            [2, 2, 3, 3],
        ]

    if gridDimension == 5:
        numberOfSubgrids = 5

        zMap = [
            [0, 0, 1, 1, 1],
            [0, 0, 4, 1, 1],
            [0, 4, 4, 4, 3],
            [2, 2, 4, 3, 3],
            [2, 2, 2, 3, 3],
        ]

    if gridDimension == 6:
        numberOfSubgrids = 6

        zMap = [
            [0, 0, 0, 1, 1, 1],
            [0, 0, 0, 1, 1, 1],
            [2, 2, 2, 3, 3, 3],
            [2, 2, 2, 3, 3, 3],
            [4, 4, 4, 5, 5, 5],
            [4, 4, 4, 5, 5, 5],
        ]

    if gridDimension == 9:
        numberOfSubgrids = 9

        zMap = [
            [0, 0, 0, 1, 1, 1, 2, 2, 2],
            [0, 0, 0, 1, 1, 1, 2, 2, 2],
            [0, 0, 0, 1, 1, 1, 2, 2, 2],
            [3, 3, 3, 4, 4, 4, 5, 5, 5],
            [3, 3, 3, 4, 4, 4, 5, 5, 5],
            [3, 3, 3, 4, 4, 4, 5, 5, 5],
            [6, 6, 6, 7, 7, 7, 8, 8, 8],
            [6, 6, 6, 7, 7, 7, 8, 8, 8],
            [6, 6, 6, 7, 7, 7, 8, 8, 8],
        ]

    def ix(x, y):
        return x + y * gridDimension

    def ixwn(n, x, y):
        return n + ix(x, y) * gridDimension

    DESC = Descriptor()
    with DESC as theEmbedding:
        if HEADER("queen or free"):
            # Number and no-number constants
            CV("N", gridDimension * gridDimension * gridDimension)
            CV("W", gridDimension * gridDimension * gridDimension)

            CV("R", gridDimension * gridDimension)
            CV("C", gridDimension * gridDimension)
            CV("Z", gridDimension * numberOfSubgrids)

            CV("g", gridDimension * gridDimension * gridDimension)
            C("G")

            CMP("N", "W")
            if usePositives:
                C("inc")

        CX = M("g")

        Qvars = M("G", "N")

        SG = [None] * numberOfSubgrids
        for x in range(0, gridDimension):
            for y in range(0, gridDimension):
                z = zMap[x][y]
                if SG[z] is None:
                    SG[z] = []
                SG[z].append([x, y])

        N = set([])
        Nx = [None] * gridDimension
        Ny = [None] * gridDimension
        Nn = [None] * gridDimension
        Nz = [None] * gridDimension
        W = set([])
        Wx = [None] * gridDimension
        Wy = [None] * gridDimension
        Wn = [None] * gridDimension
        Wz = [None] * gridDimension
        for k in range(0, gridDimension):
            Nx[k] = set([])
            Ny[k] = set([])
            Nn[k] = set([])
            Nz[k] = set([])
            Wx[k] = set([])
            Wy[k] = set([])
            Wn[k] = set([])
            Wz[k] = set([])

        for n in range(0, gridDimension):
            for x in range(0, gridDimension):
                for y in range(0, gridDimension):
                    Nnxy = F("N", ixwn(n, x, y))
                    Nx[x].add(Nnxy)
                    Ny[y].add(Nnxy)
                    Nn[n].add(Nnxy)
                    N.add(Nnxy)

                    Wnxy = F("W", ixwn(n, x, y))
                    Wx[x].add(Wnxy)
                    Wy[y].add(Wnxy)
                    Wn[n].add(Wnxy)
                    W.add(Wnxy)

        for z in range(0, numberOfSubgrids):
            for x, y in SG[z]:
                for n in range(0, gridDimension):
                    Nnxy = F("N", ixwn(n, x, y))
                    Nz[z].add(Nnxy)
                    Wnxy = F("W", ixwn(n, x, y))
                    Wz[z].add(Wnxy)

        theEmbedding.REGION = 1  # --------------------------------------------------

        # define R and C
        for n in range(0, gridDimension):
            for x in range(0, gridDimension):
                for y in range(0, gridDimension):
                    ADD(
                        INC(
                            M(F("R", ix(n, x)), F("C", ix(n, y))), F("N", ixwn(n, x, y))
                        )
                    )

        # define Z
        for z in range(0, numberOfSubgrids):
            for x, y in SG[z]:
                for n in range(0, gridDimension):
                    ADD(INC(F("Z", ix(n, z)), F("N", ixwn(n, x, y))))

        # F("R", ix(n, x)) can only be produced by numbers n in the row x
        for n in range(0, gridDimension):
            for x in range(0, gridDimension):
                aux = N - Nx[x] & Nn[n]
                ADD(EXC(F("R", ix(n, x)), M(*list(aux), "W")))

        # F("C", ix(n, y)) can only be produced by numbers n in the column y
        for n in range(0, gridDimension):
            for y in range(0, gridDimension):
                aux = N - Ny[y] & Nn[n]
                ADD(EXC(F("C", ix(n, y)), M(*list(aux), "W")))

        # F("Z", ix(n, z)) can only be produced by numbers n in the subgrid z
        for n in range(0, gridDimension):
            for z in range(0, gridDimension):
                aux = N - Nz[z] & Nn[n]
                ADD(EXC(F("Z", ix(n, z)), M(*list(aux), "W")))

        # W from N
        # A number n at x y produces W in the rest of the row column and subgrid
        for z in range(0, numberOfSubgrids):
            for x, y in SG[z]:
                for n in range(0, gridDimension):
                    Nnxy = F("N", ixwn(n, x, y))
                    Wnxy = F("W", ixwn(n, x, y))
                    aux = (Wx[x] | Wy[y] | Wz[z]) & Wn[n] - set([Wnxy])

                    ADD(INC(M(*list(aux)), M(Nnxy, "G")))

        # A number n at x y produces W in the sam cell for all the other numbers
        for n in range(0, gridDimension):
            for x in range(0, gridDimension):
                for y in range(0, gridDimension):
                    Nnxy = F("N", ixwn(n, x, y))
                    aux = (Wx[x] & Wy[y]) & (W - Wn[n])

                    ADD(INC(M(*list(aux)), M(Nnxy, "G")))

                    #  W in the sam cell for all the other numbers produce a number n
                    ADD(INC(Nnxy, M(M(*list(aux)), "G")))

        # N from W
        # A number n at x y is produced if W is set either in the rest of the
        # row or the rest of the column or the rest of the subgrid
        for z in range(0, numberOfSubgrids):
            for x, y in SG[z]:
                for n in range(0, gridDimension):
                    Nnxy = F("N", ixwn(n, x, y))
                    Wnxy = F("W", ixwn(n, x, y))

                    aux = Wx[x] & Wn[n] - set([Wnxy])
                    ADD(INC(Nnxy, M(*list(aux), "G")))

                    aux = Wy[y] & Wn[n] - set([Wnxy])
                    ADD(INC(Nnxy, M(*list(aux), "G")))

                    aux = Wz[z] & Wn[n] - set([Wnxy])
                    ADD(INC(Nnxy, M(*list(aux), "G")))

        # Queen per row and per column
        theEmbedding.REGION = 2  # --------------------------------------------------

        # Fix numbers
        if gridDimension == 4:
            # invent sudoku
            example = [[0, 1, 0, 0], [2, 3, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]

            fixed = [[1, 1, 0, 0], [1, 1, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]

        if gridDimension == 5:
            # invent sudoku
            example = [
                [0, 1, 0, 0, 0],
                [2, 3, 0, 0, 0],
                [4, 0, 0, 0, 0],
                [0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0],
            ]

            fixed = [
                [1, 1, 0, 0, 0],
                [1, 1, 0, 0, 0],
                [1, 0, 0, 0, 0],
                [0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0],
            ]

        if gridDimension == 6:
            # invent sudoku
            example = [
                [0, 1, 2, 0, 0, 0],
                [3, 4, 5, 0, 0, 0],
                [0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0],
            ]

            fixed = [
                [1, 1, 1, 0, 0, 0],
                [1, 1, 1, 0, 0, 0],
                [0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0],
            ]

        if gridDimension == 9:
            if False:
                # resolve sudoku
                example = [
                    [5, 4, 3, 9, 2, 1, 8, 7, 6],
                    [2, 1, 9, 6, 8, 7, 5, 4, 3],
                    [8, 7, 6, 3, 5, 4, 2, 1, 9],
                    [9, 8, 7, 4, 6, 5, 3, 2, 1],
                    [3, 2, 1, 7, 9, 8, 6, 5, 4],
                    [6, 5, 4, 1, 3, 2, 9, 8, 7],
                    [7, 6, 5, 2, 4, 3, 1, 9, 8],
                    [4, 3, 2, 8, 1, 9, 7, 6, 5],
                    [1, 9, 8, 5, 7, 6, 4, 3, 2],
                ]

                fixed = [
                    [1, 1, 0, 0, 1, 0, 1, 0, 1],
                    [0, 1, 1, 0, 0, 1, 0, 0, 1],
                    [0, 0, 0, 1, 0, 0, 0, 1, 1],
                    [1, 0, 0, 1, 0, 1, 0, 1, 0],
                    [0, 0, 1, 0, 0, 0, 1, 0, 1],
                    [1, 0, 1, 0, 1, 1, 0, 1, 0],
                    [0, 1, 0, 0, 0, 0, 1, 1, 0],
                    [1, 0, 1, 0, 0, 1, 0, 0, 1],
                    [0, 1, 0, 0, 1, 0, 1, 0, 1],
                ]

                # Transform from standar n in (1, dim) to of n in (0, dim - 1)
                for x in range(0, gridDimension):
                    for y in range(0, gridDimension):
                        example[x][y] -= 1
            else:
                # invent sudoku
                example = [
                    [0, 1, 2, 0, 0, 0, 0, 0, 0],
                    [3, 4, 5, 0, 0, 0, 0, 0, 0],
                    [6, 7, 8, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0],
                ]

                fixed = [
                    [1, 1, 1, 0, 0, 0, 0, 0, 0],
                    [1, 1, 1, 0, 0, 0, 0, 0, 0],
                    [1, 1, 1, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0],
                ]

        for x in range(0, gridDimension):
            for y in range(0, gridDimension):
                if fixed[x][y] == 1:
                    n = example[x][y]
                    ADD(INC(F("N", ixwn(n, x, y)), "G"))

        # Both, number and no-number are not allowed in the grid
        if usePositives:
            ADD(INC("inc", M(T("N", _i), T("W", _i))))
            ADD(EXC("inc",  "G"))
        else:
            ADD(EXC(M(T("N", _i), T("W", _i)), "G"))

        # Reuqire all columns, rows and grids to have every number
        ADD(INC(M("R", "C", "Z"), "G"))

        # (optional) A cell cannot have all Ws values
        for x in range(0, gridDimension):
            for y in range(0, gridDimension):
                aux = Wx[x] & Wy[y]
                ADD(EXC(M(*list(aux)), "G"))

        # Make the embdding explicit
        ADD(INC(T("N", _i), M("G", T("g", _i))))

        return {
            "descriptor": DESC,
            "constants": [el.const for el in F("constants pending transfer to algebra").r],  # fmt:skip
            "constantsNames": [el.key for el in F("constants pending transfer to algebra").r],  # fmt:skip
            "positiveDuples": [(el.rl_L.s, el.rl_H.s, el.region, el.treatAsHypothesis) for el in F("inclusions").r],  # fmt:skip
            "negativeDuples": [(el.rl_L.s, el.rl_H.s, el.region, el.treatAsHypothesis) for el in F("exclusions").r],  # fmt:skip
            "contextConstants": S(CX).s,
            "GConstants": S(F("G")).s,
            "NConstants": [el.const for el in F("N").v],
            "CMPConstants": {el.const: CMP(el).const for el in F("N").v + F("W").v},
            "WConstants": [el.const for el in F("W").v],
            }
