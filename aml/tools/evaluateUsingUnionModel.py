# Algebraic AI - 2025
# Go to github.com/Algebraic-AI for full license details.


def evaluateUsingUnionModelAtOptimalCutoff(rels, balance, region):
    print("Result ----------------")
    scope = 0
    table = {}
    numNegatives = 0
    numPositives = 0
    for r in rels:
        if (region == -1) or (r.region == region):
            disc = r.wL.las - r.wH.las
            scope = max(scope, len(disc))
            tkey = str(len(disc))
            if not tkey in table:
                table[tkey] = [0, 0]
            v = table[tkey]
            if r.positive:
                numPositives += 1
                w = [v[0] + 1, v[1]]
            else:
                numNegatives += 1
                w = [v[0], v[1] + 1]
            table[tkey] = w.copy()

    if balance == -1:
        balance = numNegatives / numPositives
        print(f"auto balance: {balance}")

    histogramPlus = [0] * (scope + 1)
    histogramMinus = [0] * (scope + 1)
    for dSize in range(0, scope + 1):
        tkey = str(dSize)
        if tkey in table:
            v = table[tkey]
        else:
            v = [0, 0]
        histogramPlus[dSize] = v[0] / max(numPositives, 1)
        histogramMinus[dSize] = v[1] / max(numNegatives, 1)

    tprx = [0] * (scope + 2)
    tprcount = 0
    for dSize in range(0, scope + 1):
        tprx[dSize] = tprcount
        tprcount += histogramPlus[dSize]
    tprx[scope + 1] = tprcount

    fprx = [0] * (scope + 2)
    fprcount = 0
    for dSize in range(0, scope + 1):
        fprx[dSize] = fprcount
        fprcount += histogramMinus[dSize]
    fprx[scope + 1] = fprcount

    fpr = 0
    tpr = 0
    area = 0
    for dSize in range(0, scope + 2):
        intervalx = fprx[dSize] - fpr
        intervaly = tprx[dSize] - tpr
        area += tpr * intervalx  # squared part
        area += intervaly * intervalx / 2  # triangulart part
        fpr = fprx[dSize]
        tpr = tprx[dSize]
    print(f"AUC: {area}")

    sumPlus = 0
    sumMinus = 0
    bestAverage = 0
    misses = -1
    f1 = 0
    f1n = 0
    for dSize in range(0, scope + 1):
        sumPlus += histogramPlus[dSize]
        sumMinus += histogramMinus[dSize]
        histogramPlus[dSize] = sumPlus
        histogramMinus[dSize] = sumMinus
        correctAverage = (
            balance * (1 - histogramMinus[dSize]) + histogramPlus[dSize]
        ) / (1 + balance)
        if correctAverage > bestAverage:
            bestAverage = correctAverage
            misses = dSize + 1
            # calc F1
            TN = (1 - histogramMinus[dSize]) * numNegatives
            TP = histogramPlus[dSize] * numPositives
            FP = histogramMinus[dSize] * numNegatives
            FN = (1 - histogramPlus[dSize]) * numPositives
            f1 = TP / max(1, (TP + 0.5 * (FP + FN)))
            f1n = TN / max(1, (TN + 0.5 * (FP + FN)))
    print(
        f"TN {TN}",
        f"TP {TP}",
        f"FP {FP}",
        f"FN {FN}",
        f"+ {numPositives}",
        f"- {numNegatives}",
        f"at {misses} misses",
    )
    print(f"F1 scores: {f1} {f1n} at {misses} misses")
    print(f"Accuracy {bestAverage} Error: {1 - bestAverage} at {misses} misses")

    minError = 1 - bestAverage
    minError = int(minError * 10000) / 10000
    result = f"Error: {minError} at optimal cutoff {misses}"

    returnval = result, minError, misses

    # Optimal f1 score
    f1 = 0
    f1n = 0
    missesForBestF1n = -1
    missesForBestF1 = -1
    for dSize in range(0, scope + 1):
        TN = (1 - histogramMinus[dSize]) * numNegatives
        TP = histogramPlus[dSize] * numPositives
        FP = histogramMinus[dSize] * numNegatives
        FN = (1 - histogramPlus[dSize]) * numPositives
        thisf1 = TP / (TP + 0.5 * (FP + FN))
        thisf1n = TN / (TN + 0.5 * (FP + FN))

        if thisf1 > f1:
            f1 = thisf1
            missesForBestF1 = dSize + 1
        if thisf1n > f1n:
            f1n = thisf1n
            missesForBestF1n = dSize + 1

    print(f"optimal f1 score + class: {f1} at {missesForBestF1} misses")
    print(f"optimal f1 score - class: {f1n} at {missesForBestF1n} misses")
    print("-----------------------")

    return returnval


def evaluateUsingUnionModel(rels, region, misses):
    numNegatives = 0
    numPositives = 0
    fp = 0
    fn = 0
    for r in rels:
        if (region == -1) or (r.region == region):
            disc = r.wL.las - r.wH.las
            assignedPositive = len(disc) < misses
            if r.positive:
                numPositives += 1
                if not assignedPositive:
                    fn += 1
            else:
                numNegatives += 1
                if assignedPositive:
                    fp += 1

    FPR = fp / numNegatives
    FNR = fn / numPositives
    TP = numPositives - fn
    TN = numNegatives - fp

    Error = (fp + fn) / (numPositives + numNegatives)
    ACC = (TP + TN) / (numPositives + numNegatives)

    TPR = TP / numPositives
    sensitivity = TPR
    specificity = 1 - FPR
    avAUC = (sensitivity + specificity) / 2

    print("misses: ", misses)
    print("numPositives: ", numPositives)
    print("numNegatives: ", numNegatives)
    print("FPR: ", FPR)
    print("FNR: ", FNR)
    print("Error: ", Error)
    print("ACC: ", ACC)
    print("sensitivity: ", sensitivity)
    print("specificity: ", specificity)
    print("(sensitivity + specificity) / 2: ", avAUC)
    result = f"Error: {Error} at cutoff 1"
    returnval = result, Error
    print("-----------------------")
    return returnval
