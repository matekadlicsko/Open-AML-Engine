# -*- coding: utf-8 -*-
"""
Created on Tue Mar 10 13:27:58 2020

@author: Fernando
"""

import random
import os
import struct
import sys
import numpy as np

# import array
from array import array as pyarray


path = "./mnist_datasets"


class datasetType:
    test = 0
    training = 1
    validation = 2


def printImageOfDigit(image, rows, cols):
    print("\n")
    j = 0
    for r in range(rows):
        auxstring = ""
        for c in range(cols):
            if image[j] > 128:
                auxstring += "#"
            else:
                auxstring += " "
            j += 1
        print(auxstring)


def load_mnist(dataset="training", validationSize=0, digits=np.arange(10)):
    print("<LOADING MNIST dataset", end="", flush=True)

    if dataset == "training":
        fname_img = os.path.join(path, "train-images-idx3-ubyte")
        fname_lbl = os.path.join(path, "train-labels-idx1-ubyte")
    elif dataset == "testing":
        fname_img = os.path.join(path, "t10k-images-idx3-ubyte")
        fname_lbl = os.path.join(path, "t10k-labels-idx1-ubyte")
    elif dataset == "validation":
        fname_img = os.path.join(path, "train-images-idx3-ubyte")
        fname_lbl = os.path.join(path, "train-labels-idx1-ubyte")
    else:
        raise ValueError("dataset must be 'testing' or 'training'")

    flbl = open(fname_lbl, "rb")
    magic_nr, size = struct.unpack(">II", flbl.read(8))
    lbl = pyarray("b", flbl.read())
    flbl.close()

    fimg = open(fname_img, "rb")
    magic_nr, size, rows, cols = struct.unpack(">IIII", fimg.read(16))
    img = pyarray("B", fimg.read())
    fimg.close()

    firstValidationIndex = size - validationSize

    if dataset == "training":
        initialIndex = 0
        ind = [k for k in range(size) if (k < firstValidationIndex) and lbl[k] in digits]  # fmt:skip
    elif dataset == "testing":
        initialIndex = 0
        ind = [k for k in range(size) if lbl[k] in digits]
    elif dataset == "validation":
        initialIndex = firstValidationIndex
        ind = [k for k in range(size) if (k >= firstValidationIndex) and lbl[k] in digits]  # fmt:skip

    N = len(ind)
    images = [None] * N
    labels = np.zeros((N, 1), dtype=np.int8)
    for i in range(N):
        images[i] = img[ind[i] * rows * cols : (ind[i] + 1) * rows * cols]
        labels[i] = lbl[ind[i]]

    labels = [label[0] for label in labels]
    print(">")
    return images, labels, initialIndex


def getTable(labels):
    ret = [[] for x in range(10)]

    i = 0
    for l in labels:
        ret[labels[i]].append(i)
        i += 1
    return ret


def getCounterTable(labels):
    ret = [[] for x in range(10)]

    i = 0
    for l in labels:
        d = labels[i]
        for j in range(10):
            if j != d:
                ret[j].append(i)
        i += 1
    return ret


def getFullTable(labels):
    ret = [i for i in range(0, len(labels))]
    return ret


# *****************************************************************************


class mnistGenerator:
    def __init__(self, VALIDATIONSIZE=0):
        self.VALIDATIONSIZE = VALIDATIONSIZE
        self.__loaded = False
        self.mnist_testing = None
        self.mnist_training = None
        self.mnist_validation = None

        self.__i_training = 0
        self.__ci_training = 0
        self.__f_training = 0
        self.__i_testing = 0
        self.__ci_testing = 0
        self.__f_testing = 0
        self.__i_validation = 0
        self.__ci_validation = 0
        self.__f_validation = 0

    def createTables(self):
        self.mnist_testing = list(load_mnist(dataset="testing"))
        self.mnist_testing.append(getTable(self.mnist_testing[1]))
        self.mnist_testing.append(getCounterTable(self.mnist_testing[1]))
        self.mnist_testing.append(getFullTable(self.mnist_testing[1]))

        self.mnist_training = list(
            load_mnist(dataset="training", validationSize=self.VALIDATIONSIZE)
        )
        self.mnist_training.append(getTable(self.mnist_training[1]))
        self.mnist_training.append(getCounterTable(self.mnist_training[1]))
        self.mnist_training.append(getFullTable(self.mnist_training[1]))

        if self.VALIDATIONSIZE != 0:
            self.mnist_validation = list(
                load_mnist(dataset="validation", validationSize=self.VALIDATIONSIZE)
            )
            self.mnist_validation.append(getTable(self.mnist_validation[1]))
            self.mnist_validation.append(getCounterTable(self.mnist_validation[1]))
            self.mnist_validation.append(getFullTable(self.mnist_validation[1]))

        self.__loaded = True

    def getRange(self, selectDigit=None, complement=False, typeOfDataset=1):
        if self.__loaded == False:
            self.createTables()

        if selectDigit is None and complement == True:
            print("incompatible setting")
            sys.exit()

        if typeOfDataset == 0:
            # TEST
            images, labels, initialIndex, table, ctable, ftable = self.mnist_testing
        elif typeOfDataset == 1:
            # TRAINING
            images, labels, initialIndex, table, ctable, ftable = self.mnist_training
        elif typeOfDataset == 2:
            # VALIDATION
            images, labels, initialIndex, table, ctable, ftable = self.mnist_validation
        else:
            raise ValueError("dataset type not valid")

        if selectDigit is None:
            return len(ftable)
        else:
            if complement:
                return len(ctable[selectDigit])
            else:
                return len(table[selectDigit])

    def getNextDigit(self, selectDigit=None, complement=False, typeOfDataset=1):
        if self.__loaded == False:
            self.createTables()

        if selectDigit is None and complement == True:
            print("incompatible setting")
            sys.exit()

        if typeOfDataset == 0:
            # TEST
            images, labels, initialIndex, table, ctable, ftable = self.mnist_testing

            if selectDigit is None:
                pos = self.__f_testing
                self.__f_testing += 1
            else:
                if complement:
                    pos = self.__ci_testing
                    self.__ci_testing += 1
                else:
                    pos = self.__i_testing
                    self.__i_testing += 1

        elif typeOfDataset == 1:
            # TRAINING
            images, labels, initialIndex, table, ctable, ftable = self.mnist_training

            if selectDigit is None:
                pos = self.__f_training
                self.__f_training += 1
            else:
                if complement:
                    pos = self.__ci_training
                    self.__ci_training += 1
                else:
                    pos = self.__i_training
                    self.__i_training += 1

        elif typeOfDataset == 2:
            # VALIDATION
            images, labels, initialIndex, table, ctable, ftable = self.mnist_validation

            if selectDigit is None:
                pos = self.__f_validation
                self.__f_validation += 1
            else:
                if complement:
                    pos = self.__ci_validation
                    self.__ci_validation += 1
                else:
                    pos = self.__i_validation
                    self.__i_validation += 1
        else:
            print("dataset type not valid")
            sys.exit()

        if selectDigit is None:
            tableDigit = ftable
        else:
            if complement:
                tableDigit = ctable[selectDigit]
            else:
                tableDigit = table[selectDigit]

        if pos % len(tableDigit) == 0:
            random.shuffle(tableDigit)
        i = tableDigit[pos % len(tableDigit)]

        if selectDigit is not None:
            if (labels[i] == selectDigit) == complement:
                raise ValueError("dataset type not valid")

        return images[i], labels[i], i + initialIndex
