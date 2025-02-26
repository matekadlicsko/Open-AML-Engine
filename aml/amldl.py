# Algebraic AI - 2025
# Go to github.com/Algebraic-AI for full license details.

import enum
import random
import numpy as np


def load_embedding(embedding, *args, **kwargs):
    import sys
    import importlib.util

    spec = importlib.util.spec_from_file_location("embeddingFile", embedding)
    module = importlib.util.module_from_spec(spec)
    sys.modules["embeddingFile"] = module
    spec.loader.exec_module(module)
    return module.embedding(*args, **kwargs)


### Types of Elements
@enum.unique
class isA(enum.Enum):
    Constant = enum.auto()
    Reference = enum.auto()
    Duple = enum.auto()
    Set = enum.auto()
    Vector = enum.auto()
    RVector = enum.auto()
    TVector = enum.auto()


### Element class
class E:
    def __init__(self, name=None):
        """Create an Element

        Args:
            name (str), optional: If provided, the Element is stored and can be
                found using F(name)

        Returns:
            E: The Element
        """

        if self.desc is None:
            raise Exception(
                """Attempting to crete an element of type E.
                These can only be used and created within a Descriptor context.
                Try wrapping your call with 'with Descriptor() as embedding:'."""
            )

        if isinstance(self.desc, Descriptor):
            if name is None:
                self.region = self.desc.REGION
                self.externalReference = self.desc.EXTERNAL_REFERENCE
                self.enforceDuple = self.desc.ENFORCE
                self.doNotCount = not self.desc.COUNT
                self.store = self.desc.STORE | self.desc.TREAT_AS_STORABLE_HYPOTHESIS
                self.treatAsHypothesis = (
                    self.desc.TREAT_AS_HYPOTHESIS
                    | self.desc.TREAT_AS_STORABLE_HYPOTHESIS
                )
                self.canFail = self.desc.CAN_FAIL

                self.type = None
                self.key = None

                self.const = None

                self.rf_reference = None

                self.rl_inclusion = None
                self.rl_L = None
                self.rl_H = None

                self.r = []
                self.t = []
                self.v = []
                self.s = set()

            elif isinstance(name, str):
                anItem = F(name)
                if anItem is None:
                    self.__init__()
                    self.key = name
                    self.desc.elementMap[name] = self
                else:
                    raise KeyError(name + " already exists")
            else:
                raise TypeError("Second argument of E() must be None or a string")
        else:
            raise TypeError("First argument of E() must be a Descriptor")

    def getDimension(self):
        if self.type == isA.Vector:
            return len(self.v)
        elif self.type == isA.TVector:
            return len(self.t)
        elif self.type == isA.RVector:
            return len(self.r)
        else:
            raise TypeError("Cannot getDimension of non array")

    def getComponent(self, index):
        if index < self.getDimension():
            if self.type is isA.Vector:
                return self.v[index]
            elif self.type is isA.TVector:
                return self.t[index]
            elif self.type is isA.RVector:
                return self.r[index]
            else:
                raise TypeError("The element must be a vector")
        else:
            raise IndexError("Index out of bounds")


# Return true if first time name is seen
def HEADER(areaName):
    """Register a new Header

    Args:
        areaName (str): Header name

    Returns:
        bool: return True if new Header, False if the Header already exists.
    """

    if HEADER.desc is None:
        raise Exception(
            """HEADER can only be used within a Descriptor context.
            Try using 'with Descriptor() as embedding:'."""
        )

    name = f"HEADER({ areaName })"
    if name in HEADER.desc.headerNames:
        return False
    else:
        HEADER.desc.headerNames.add(name)
        return True


# Find hashed item
def F(elementID, compIndex=None):
    """Find a stored Element

    Args:
        elementID (str): name of the stored Element to fetch
        elementID (int): ID of the Element to fetch, the name is in the form
            `CONSTANT(elementID)`
        compIndex (int), optional: when elementID is an array, compIndex is used
            to fetch a particular Element in that array by index

    Returns:
        E: the stored Element
        None: if the Element cannot be found
    """

    if F.desc is None:
        raise Exception(
            """F can only be used within a Descriptor context.
            Try using 'with Descriptor() as embedding:'."""
        )

    if compIndex is None:
        if isinstance(elementID, str):
            if elementID in F.desc.elementMap:
                return F.desc.elementMap[elementID]
            else:
                return None
        elif isinstance(elementID, int):
            cname = f"CONSTANT({ elementID })"
            anItem = F(cname)
            if anItem is None:
                return None
            elif anItem.type is not isA.Reference:
                raise TypeError("Element is not a reference")
            else:
                return anItem.rf_reference
        else:
            raise TypeError("First argument of F must be an integer or a string")
    elif isinstance(compIndex, int):
        if isinstance(elementID, str):
            if elementID in F.desc.elementMap:
                anItem = F.desc.elementMap[elementID]
                return anItem.getComponent(compIndex)  # It checks out of bounds
            else:
                return None
        elif isinstance(elementID, E):
            return elementID.getComponent(compIndex)
        else:
            raise TypeError("First argument of F must be an Element or a string")
    else:
        raise TypeError("Second argument of F, if defined, must be an integer")


# Create empty r-vector
# Create empty r-vector recoverable by name
def V(name=None):
    """Create an Element of type RVector

    Args:
        name (str), optional: If provided, the Element is stored and can be
            found using F(name)

    Returns:
        E: The Element
    """

    if name is None:
        aNewItem = E()
    elif isinstance(name, str):
        aNewItem = E(name)
    else:
        raise TypeError("First argument of V() must be None or a string")

    aNewItem.type = isA.RVector
    return aNewItem


# Appends item to r-vector
def APP(toItem, anItem):
    """Append an Element to an RVector

    Args:
        toItem (E): The target RVector
        anItem (E): The Element to be appended
    """

    if toItem.type is isA.RVector:
        toItem.r.append(anItem)
    else:
        raise TypeError("The first argument of APP must be an r-vector")


# Assign to a constant an store in hash map
def C(anItem):
    """Create an Element of type Constant

    Takes a new name or a nameless Element, stores it and adds it to the
        'constants pending transfer to algebra' V vector

    Args:
        anItem (str): Name of the Constant to be returned
        anItem (E): Nameless Element

    Returns:
        E: The Constant

    Raises:
        KeyError: If anItem already exists and has been stored

    """

    if C.desc is None:
        raise Exception(
            """C can only be used within a Descriptor context.
            Try using 'with Descriptor() as embedding:'."""
        )

    if isinstance(anItem, str):
        if F(anItem) is None:
            return C(E(anItem))
        else:
            raise KeyError(anItem + " already exists")

    anItem.type = isA.Constant
    anItem.const = C.desc.newConstantID()
    cname = f"CONSTANT({ anItem.const })"
    refItem = E(cname)
    refItem.type = isA.Reference
    refItem.rf_reference = anItem
    APP(F(C.desc.PEND_TRANSF), anItem)
    C.desc.constIDToDescriptor[str(anItem.const)] = anItem
    return anItem


# Assign to a constant in chain an store in hash map
def N(field, value):
    """Create an Element of type Constant in chain
    """

    if N.desc is None:
        raise Exception(
            """C can only be used within a Descriptor context.
            Try using 'with Descriptor() as embedding:'."""
        )

    if not isinstance(value, (int, float)):
        raise Exception(
            """Value must be a number."""
        )

    if (field, value) not in N.desc.numFieldNames:
        N.desc.numFieldNames.append((field, value))

    return M(C(f"FieldUP:{field}[{value}]"), C(f"FieldDOWN:{field}[{value}]"))


# Transform into a set (no store)
def S(anItem):
    """Transform into a Set

    Take a Constant, Set, Vector, RVector or TVector and transform into a Set.

    Args:
        anItem (str): Name of the Element to be transformed

    Returns:
        E: Element of type Set that contains the identifier of all constants.
            If TVectors are used as input, the result will be a TVector of Sets.

    """

    if isinstance(anItem, str):
        return S(F(anItem))
    else:
        return __unaryBase(anItem, __S)


def __S(anItem):
    aNewItem = E()
    aNewItem.type = isA.Set

    if anItem.type is isA.Constant:
        aNewItem.s.add(anItem.const)

    elif (anItem.type is isA.Vector) or (anItem.type is isA.RVector):
        dimension = anItem.getDimension()
        for k in range(dimension):
            if anItem.getComponent(k).type is isA.Constant:
                constID = anItem.getComponent(k).const
                aNewItem.s.add(constID)
            else:
                aNewItem.s |= S(anItem.getComponent(k)).s

    elif anItem.type is isA.Set:
        aNewItem.s = anItem.s.copy()

    else:
        raise TypeError("No rule to make " + str(anItem.type) + " into a set")

    return aNewItem


# Create a t-vector (no store)
# Transform vector into a t-vector (no store)
def T(anItem=None, varIndex=None):

    if anItem is None:
        raise TypeError("First argument of T cannot be None")

    elif isinstance(anItem, str):
        return T(F(anItem), varIndex)

    elif (varIndex is not None) and (
        anItem.type is isA.Vector
        or anItem.type is isA.RVector
        or anItem.type is isA.Set
    ):
        anotherItem = T(anItem)
        anotherItem.t_varIndex = varIndex
        return anotherItem

    elif (varIndex is not None) and (anItem.type is isA.TVector):
        dimension = len(anItem.t)
        aNewItem = T(dimension)
        aNewItem.t_varIndex = anItem.t_varIndex
        for k in range(dimension):
            if isinstance(anItem.t[k], int):
                raise TypeError("Int cannot be indexed")

            aNewItem.t[k] = T(anItem.t[k], varIndex)
        return aNewItem

    elif isinstance(anItem, int):
        dimension = anItem
        aNewItem = E()
        aNewItem.type = isA.TVector
        aNewItem.t_varIndex = 0
        aNewItem.t = [None] * dimension
        return aNewItem

    else:
        return __unaryBase(anItem, __T)


def __T(anItem):
    if (anItem.type is isA.Vector) or (anItem.type is isA.RVector):
        dimension = anItem.getDimension()
        if dimension <= 0:
            raise IndexError("T vector with 0 length")
        aNewItem = T(dimension)
        for k in range(dimension):
            component = anItem.getComponent(k)
            aNewItem.t[k] = component
        return aNewItem
    elif anItem.type is isA.Set:
        dimension = len(anItem.s)
        print("The dimension was", dimension)
        if dimension <= 0:
            raise IndexError("T vector with 0 length")
        aNewItem = T(dimension)
        k = 0
        for component in anItem.s:
            aNewItem.t[k] = C.desc.constIDToDescriptor[str(component)]
            k += 1
        return aNewItem
    else:
        raise TypeError(
            "Argument of T must be an vector or string identifier of a vector"
        )


# Create and store vector of constants
def CV(name, dimension):
    """Create a Vector of Constants

    Create a Vector of new Constants of length `dimension`. The Vector and
        the individual Constants are stored.
    If `name` already exists, it returns the stored Element.

    Args:
        name (str): Name of the Vector
        dimension (int): Number of Constants to be created

    Returns:
        E: The Vector
    """

    if not isinstance(name, str) and not isinstance(dimension, int):
        raise TypeError("Arguments of CV must be a string and an integer")

    anItem = F(name)
    if anItem is not None:
        return anItem
    else:
        anItem = E(name)
        anItem.type = isA.Vector
        for k in range(dimension):
            anItem.v.append(E())
            component = C(anItem.v[-1])
            component.key = f"{ name }[{ k }]"

    return anItem


def M(*idItem):
    """Merge two or more Elements into a new Set

    It takes two or more comma-separated idItem's.
    The new set is not stored.

    Args:
        idItem (str): name of the Elements to merge
        idItem (E): identifier of the Elements to merge

    Returns:
        E: Element of type Set containg all elements in idItem. If TVectors
            are used as input, the result will be a TVector of Sets.
    """

    if isinstance(idItem[0], str):
        anItem = F(idItem[0])
    else:
        anItem = idItem[0]

    for item in idItem[1:]:
        if isinstance(item, str):
            anotherItem = F(item)
        else:
            anotherItem = item
        anItem = __binaryBase(anItem, anotherItem, __M)
    return anItem


def __M(itemA, itemB):
    sItemA = S(itemA)
    sItemB = S(itemB)
    if sItemA.type is isA.Set and sItemB.type is isA.Set:
        anItem = E()
        anItem.type = isA.Set
        anItem.s = set.union(sItemA.s, sItemB.s)
        return anItem
    else:
        raise TypeError(f"Expected items to be { isA.Set }")


# Set items as mutually complementaries
# Create complementary and store duple in hash map
def CMP(itemA, itemB=None):
    """Set two Elements as mutually complementaries
        or query the complementary of an Element

    If only itemA is provided, it will query its complementary if already
    registered.
    If both itemA and itemB are provided, they are registerd as complementary
    Elements

    Args:
        itemA (str): name of the Element to set complementary or query
        itemA (E): identifier of the Element
        itemB (str): name of the Element to set complementary
        itemB (E): identifier of the Element

    """

    if itemB is None:
        if isinstance(itemA, str):
            cname = f"CMP({ itemA })"
            aux = F(cname)
            if aux is None:
                return None
            elif aux.type is isA.Reference:
                return aux.rf_reference
            else:
                raise TypeError("Element is not a reference")

        else:
            return __unaryBase(itemA, __CMP)

    else:
        if isinstance(itemA, str):
            return CMP(F(itemA), itemB)
        if isinstance(itemB, str):
            return CMP(itemA, F(itemB))

        if itemA.type != itemB.type:
            raise TypeError("Both elements must have the same type")

        if itemA.type is isA.Constant:

            cnameA = f"CMP({ itemA.key })"
            if F(cnameA) is None:
                refItemA = E(cnameA)
                refItemA.type = isA.Reference
                refItemA.rf_reference = itemB
            else:
                raise KeyError("Element already exists")

            cnameB = f"CMP({ itemB.key })"
            if F(cnameB) is None:
                refItemB = E(cnameB)
                refItemB.type = isA.Reference
                refItemB.rf_reference = itemA
            else:
                raise KeyError("Element already exists")

            APP(F(Descriptor.PEND_COMP), itemA)
            APP(F(Descriptor.PEND_COMP), itemB)

        elif itemA.type is isA.Vector:
            if len(itemA.v) != len(itemB.v):
                raise TypeError("Vectors of different length")

            dimension = len(itemA.v)
            for k in range(dimension):
                CMP(itemA.v[k], itemB.v[k])
        else:
            raise TypeError("Type not supported")


def __CMP(item):
    if item.type is isA.Constant:
        return CMP(item.key)

    elif (
        item.type is isA.Vector or item.type is isA.RVector or item.type is isA.TVector
    ):

        aNewItem = E()
        if item.type is isA.TVector:
            aNewItem.type = isA.TVector
        else:
            aNewItem.type = isA.RVector

        dimension = item.getDimension()
        for k in range(dimension):
            component = item.getComponent(k)
            if component is None:
                raise TypeError("Component was None")
            if item.type is isA.TVector:
                aNewItem.t.append(CMP(component.key))
            else:
                aNewItem.r.append(CMP(component.key))

        return aNewItem

    elif item.type is isA.Set:
        aNewItem = E()
        aNewItem.type = isA.Set

        for anItem in item.s:
            component = F(anItem)
            if component is None:
                raise TypeError("Component was None")
            elif component.type is not isA.Constant:
                raise TypeError("Component must be a constant")

            component = CMP(component)
            if component is None:
                raise TypeError("Component was None")
            elif component.type is not isA.Constant:
                raise TypeError("Component must be a constant")

            aNewItem.s.add(component.const)

        return aNewItem

    else:
        raise TypeError("Not supported type")

    raise Exception("This point should never be hit")
    # return None


# Subtract item from vector (no store)
def R(fromItem, itemIn):
    if isinstance(fromItem, str):
        return R(F(fromItem), itemIn)
    if isinstance(itemIn, int):
        return R(fromItem, F(fromItem, itemIn))

    return __binaryBase(fromItem, itemIn, __R)


def __R(fromItem, itemIn):

    aNewItem = E()
    aNewItem.type = isA.RVector
    dimension = fromItem.getDimension()
    if itemIn.type is isA.Constant:
        item = S(itemIn)
        for k in range(dimension):
            component = fromItem.getComponent(k)
            if component is None:
                raise TypeError("Component is None")
            if component.type is isA.Constant:
                if component.const not in item.s:
                    aNewItem.r.append(component)
            else:
                raise TypeError("Vector contains non constants")
    else:
        for k in range(dimension):
            component = fromItem.getComponent(k)
            if component is None:
                raise TypeError("Component is None")
            if not (component is itemIn):
                aNewItem.r.append(component)

    return aNewItem


# Get a ref vector with some of the components
def SOME(fromItem, p, atLeastOne, notAll):
    """Return an RVector with with some of the elements in fromItem

    Args:
        fromItem (str/E): name or Element of type Vector, RVector or
            TVector. Elements will be picked from this vector.
        p ([0.0 1.0]): Probability of an element to be picked
        atLeastOne (bool): if True the returned RVector will contain at least
            one Element
        notAll (bool): if True the returned RVector will strictly have fewer
            Elements than fromItem

    Returns:
        E: An RVector Element containing some Element in fromItem
    """

    if isinstance(fromItem, str):
        return SOME(F(fromItem), p, atLeastOne, notAll)

    if fromItem.getDimension() < 2 and atLeastOne and notAll:
        raise IndexError("No result for these arguments")
    if p == 1 and notAll:
        raise IndexError("No result for these arguments")
    if p == 0 and atLeastOne:
        raise IndexError("No result for these arguments")

    fromItem.desc.SOME_p = p
    fromItem.desc.SOME_atLeastOne = atLeastOne
    fromItem.desc.SOME_notAll = notAll

    return __unaryBase(fromItem, __SOME)


def __SOME(fromItem):

    aNewItem = E()
    aNewItem.type = isA.RVector

    dimension = fromItem.getDimension()

    if fromItem.desc.SOME_atLeastOne and fromItem.desc.SOME_notAll:
        length = np.random.binomial(dimension - 2, fromItem.desc.SOME_p) + 1
    elif fromItem.desc.SOME_atLeastOne and fromItem.desc.SOME_notAll:
        length = np.random.binomial(dimension - 1, fromItem.desc.SOME_p) + 1
    elif fromItem.desc.SOME_notAll:
        length = np.random.binomial(dimension - 1, fromItem.desc.SOME_p)
    else:
        length = np.random.binomial(dimension, fromItem.desc.SOME_p)

    if length < 0:
        raise IndexError("Length of SOME cannot be negative")

    indices = sorted(random.sample(range(dimension), length))

    for k in indices:
        component = fromItem.getComponent(k)
        if component is None:
            raise TypeError("Component was None")
        aNewItem.r.append(component)

    return aNewItem


# Add inclusion or exclusion to problem set
# <<
def ADD(item):
    """Add inclusions or exclusions duples to the problem

    Args:
        item (E): Element of type Duple or TVector to be registered
    """

    __unaryBase(item, __ADD)


def __ADD(item):
    if item is None:
        raise TypeError("Item was None")
    if item.type is isA.Duple:
        if item.rl_inclusion:
            APP(F(Descriptor.INCLUSIONS), item)
        else:
            APP(F(Descriptor.EXCLUSIONS), item)
    else:
        raise TypeError("Item must of type duple")


# Inclusion
def INC(itemA, itemB):
    """Define a Duple of type Inclusion between two Elements or TVectors

    Args:
        itemA, itemB (E): Element or TVector.

    Returns:
        an Element of type Duple representing an inclusion
    """
    if isinstance(itemA, str):
        return INC(F(itemA), itemB)
    if isinstance(itemB, str):
        return INC(itemA, F(itemB))

    return __binaryBase(itemA, itemB, __INC)


def __INC(itemA, itemB):
    anItem = E()
    anItem.type = isA.Duple
    anItem.rl_L = __managedSet(itemA)
    anItem.rl_H = __managedSet(itemB)
    anItem.rl_inclusion = True
    return anItem


# Exclusion
def EXC(itemA, itemB):
    """Define a Duple of type Exclusion between two Elements or TVectors

    Args:
        itemA, itemB (E): Element or TVector.

    Returns:
        an Element of type Duple representing an exclusion
    """
    if isinstance(itemA, str):
        return EXC(F(itemA), itemB)
    if isinstance(itemB, str):
        return EXC(itemA, F(itemB))

    return __binaryBase(itemA, itemB, __EXC)


def __EXC(itemA, itemB):
    anItem = E()
    anItem.type = isA.Duple
    anItem.rl_L = __managedSet(itemA)
    anItem.rl_H = __managedSet(itemB)
    anItem.rl_inclusion = False
    return anItem


# Set if not set and change owner if already a set
def __managedSet(item):
    if item.type is isA.Set:
        return item
    else:
        return S(item)


# Unary operator on TVectors
def __unaryBase(anItem, funcPointer):
    if anItem is None:
        raise TypeError("item cannot be None")

    elif anItem.type is isA.TVector:
        dimension = len(anItem.t)
        aNewItem = T(dimension)
        aNewItem.t_varIndex = anItem.t_varIndex
        for k in range(dimension):
            aux = __unaryBase(anItem.t[k], funcPointer)
            aNewItem.t[k] = aux
        return aNewItem

    else:
        return funcPointer(anItem)


# Binary operator on TVectors
def __binaryBase(itemA, itemB, funcPointer, indexIsSetDict=None):
    if itemA is None or itemB is None:
        raise TypeError("itemA or itemB are None")

    if (itemA.type is isA.TVector) or (itemB.type is isA.TVector):
        if (
            itemA.type is isA.TVector
            and itemB.type is isA.TVector
            and itemA.t_varIndex == itemB.t_varIndex
        ):
            if (indexIsSetDict is None) or (itemA.t_varIndex not in indexIsSetDict):
                if indexIsSetDict is None:
                    indexIsSetDict = {}

                dimension = len(itemA.t)
                if dimension != len(itemB.t):
                    raise IndexError("Incompatible t-vector operation")
                newItem = T(dimension)
                newItem.t_varIndex = itemA.t_varIndex  # | itemB.t_varIndex
                for k in range(dimension):
                    isd = indexIsSetDict.copy()
                    isd[itemA.t_varIndex] = k
                    newItem.t[k] = __binaryBase(
                        itemA.t[k], itemB.t[k], funcPointer, isd
                    )
                return newItem
            else:
                k = indexIsSetDict[str(itemA.t_varIndex)]
                return __binaryBase(itemA.t[k], itemB.t[k], funcPointer, indexIsSetDict)

        elif itemA.type is isA.TVector:
            if indexIsSetDict is None:
                indexIsSetDict = {}

            if itemA.t_varIndex in indexIsSetDict:
                k = indexIsSetDict[str(itemA.t_varIndex)]
                return __binaryBase(itemA.t[k], itemB, funcPointer, indexIsSetDict)

            dimension = len(itemA.t)
            newItem = T(dimension)
            newItem.t_varIndex = itemA.t_varIndex
            for k in range(dimension):
                isd = indexIsSetDict.copy()
                isd[itemA.t_varIndex] = k
                newItem.t[k] = __binaryBase(itemA.t[k], itemB, funcPointer, isd)
            return newItem

        elif itemB.type is isA.TVector:
            if indexIsSetDict is None:
                indexIsSetDict = {}

            if itemB.t_varIndex in indexIsSetDict:
                k = indexIsSetDict[str(itemB.t_varIndex)]
                return __binaryBase(itemA, itemB.t[k], funcPointer, indexIsSetDict)

            dimension = len(itemB.t)
            newItem = T(dimension)
            newItem.t_varIndex = itemB.t_varIndex
            for k in range(dimension):
                isd = indexIsSetDict.copy()
                isd[itemB.t_varIndex] = k
                newItem.t[k] = __binaryBase(itemA, itemB.t[k], funcPointer)
            return newItem

    else:
        return funcPointer(itemA, itemB)


class Descriptor:
    PEND_TRANSF = "constants pending transfer to algebra"
    PEND_COMP = "constants pending set complementary"
    INCLUSIONS = "inclusions"
    EXCLUSIONS = "exclusions"

    functions_with_descriptor = [C, N, E, F, HEADER]

    def __init__(self):
        self.REGION = 0
        self.EXTERNAL_REFERENCE = -1
        self.ENFORCE = True
        self.COUNT = True
        self.STORE = False
        self.TREAT_AS_HYPOTHESIS = False
        self.TREAT_AS_STORABLE_HYPOTHESIS = False
        self.CAN_FAIL = False

        self.SOME_p = None
        self.SOME_atLeastOne = None
        self.SOME_notAll = None

        self.headerNames = set()  # Store header names
        self.elementMap = {}
        self.numFieldNames = []
        self.constIDToDescriptor = {}
        self.lastConstantID = 0

        E.desc = self
        F.desc = self
        V(self.INCLUSIONS)
        V(self.EXCLUSIONS)
        V(self.PEND_TRANSF)
        V(self.PEND_COMP)
        E.desc = None
        F.desc = None

    ### lastConstantID helper functions
    def newConstantID(self):
        self.lastConstantID += 1
        return self.lastConstantID - 1

    def __enter__(self):
        for f in self.functions_with_descriptor:
            f.desc = self
        return self

    def __exit__(self, *args):
        for f in self.functions_with_descriptor:
            f.desc = None


### Run tests if not imported as a module
if __name__ == "__main__":
    filename = "test_cov_aml_descriptor.py"
    with open(filename) as f:
        code = compile(f.read(), filename, "exec")
        exec(code)
