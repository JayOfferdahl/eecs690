import re
import sys
import time
import collections

inputFileName = ""
outputFileName = ""
incompleteDataset = False
DEBUG = 0
PRINT_LINE_NUMBERS = 0

# Prints out an enumerable object token by token, separating tokens with a newline.
# Will print lines with link numbers starting at 0 if PRINT_LINE_NUMBERS is True
def listPrint(list):
    for index, token in enumerate(list):
        if PRINT_LINE_NUMBERS:
            print("{} ".format(index), end = "", flush = True)
        print(token)
    # Endfor
    print()

# Spin up intelliJ for good luck
def spinUpIntelliJ():
    print("Spinning up IntelliJ", end = "", flush = True)
    for i in range(0, 24):
        print(".", end = "", flush = True)
        time.sleep(.0404)
    print("Spin up complete.\n")
    time.sleep(.5)

# Parses the input file and stores all relevant information for parsing.
# Modifies the array of cases to include the universe of cases
#   Each case has a list of indicies to a dictionary key which specifies the value of the attribute
# Modifies the dictionary of attributes to include all attributes values seen
def parseFile(attributes):
    global inputFileName
    global incompleteDataset
    inputFileName= input("\nWhat is the name of the data file you want to evaluate?\t")

    while True:
        try:
            file = open(inputFileName)
            break
        except IOError:
            inputFileName = input("Error, the file could not be opened. Try again:\t\t")
    # Endwhile

    print("\nInput file accepted: [{}]\n".format(inputFileName))

    # Parse the input file to generate the universe of cases
    spinUpIntelliJ()

    skipInput = True
    readAttrs = False
    universe = []
    currentCase = []
    attr = 0

    # Skip the < a ... a d > descriptors, read in attribute names/decision name
    for line in file:
        tokens = line.split()

        for token in tokens:
            # Wait for the end of the attribute/decision descriptors
            if token == '!':
                break
            elif token == ">":
                skipInput = False
                readAttrs = True
            elif not skipInput and readAttrs:
                # Store all of the attribute names in a list
                if token == ']':
                    readAttrs = False
                elif token != '[':
                    if token not in attributes:
                        attributes.append(token)
                    else:
                        print("Error: Token already recognized.\n")
            elif not skipInput and not readAttrs:
                # Check here if there are any missing attributes (must check all tokens)
                if not incompleteDataset and (token == '?' or token == '*' or token == '-'):
                    incompleteDataset = True

                if attr >= len(attributes):
                    # Finished a case, reset attribute counter and append this list to the universe
                    attr = 0
                    universe.append(currentCase)
                    currentCase = []
                # Endif

                currentCase.append(token)
                attr += 1
            # Endif
        # Endfor
    # Endfor

    # Append the last currentCase (last line)
    if len(currentCase) > 0:
        universe.append(currentCase)

    # DEBUG
    if DEBUG:
        listPrint(universe)

    print("Input file case list parsing complete.")
    print("There are {} total cases.\n".format(len(universe)))

    if incompleteDataset:
        print("***This dataset is incomplete; using concept approximations.\n")

    # return the input dataset
    return universe

# Captures user input to determine which rule type to calculate
# Choice 1: Calculates the set of certain rules
# Choice 2: Calculates the set of possible rules
# Returns the choice of the user
def getRuleType():
    print("What do you want to calculate?\n   1. Certain Rules\n   2. Possible Rules\n")

    # While invalid input from the user (out of bounds or of wrong type)
    while True:
        try:
            choice = int(input("Choice: "))

            if choice >= 1 and choice <= 2:
                break
        except ValueError:
            print("Please enter a number.")
    # Endwhile

    print("\nChoice {} accepted.\n".format(choice))

    rule = "certain" if choice == 1 else "possible"
    print("Calculating {} rules from dataset: [{}]\n".format(rule, inputFileName))

    return choice

# Determine what type each attribute belongs to
# Type 1: Symbolic
# Type 2: Numeric
# Type 3: Missing (If this happens, the attribute should be tossed!)
# Returns a list of the attribute types
def attributeTypes(universe, attributes):
    types = []

    decimal = "-?[0-9]+(\.[0-9]+)?"
    type1 = 0
    type2 = 0

    # For every attribute, find its type
    for i in range(0, len(attributes) - 1):
        case = 0

        # Cycle through this attribute in each case until a valid type is found
        while True:
            attr = universe[case][i]

            # Matches a symbolic type
            match = re.fullmatch(decimal + "\.\." + decimal + "|[A-Za-z]+", attr)
            if match != None:
                types.append(1)
                type1 += 1
                break

            match = re.fullmatch(decimal, attr)
            if match != None:
                types.append(2)
                type2 += 1
                break

            case += 1
            if case == len(universe):
                print("Error: type 3 attribute.\n")
        # Endwhile
    # Endfor

    print("Attribute type evaluation complete.")
    print("There are {} total attributes.\n".format(len(attributes) - 1))
    print("There are {} symbolic attributes, and {} numeric attributes.\n".format(type1, type2))
    
    # Print out the attribute names and their corresponding types
    if DEBUG:
        for i in range(0, len(types)):
            print("{}:{}".format(attributes[i], types[i]))
        print()

    return types

# Computes the concepts for the given universe (sets of distinct cases with the same decision)
def calculateConcepts(universe):
    concepts = collections.OrderedDict()

    # For every case in the universe, add the case number to the concept set it belongs
    for index, case in enumerate(universe):
        decision = case[-1]

        if decision in concepts:
            concepts[decision].add(index)
        else:
            concepts[decision] = set([index])
    # Endfor

    # For simplicity, sort each concept
    for key, value in concepts.items():
        concepts[key] = sorted(value, key = int)

    return concepts

# Computes the specified values for the given concept. If a value for the given attribute index
# is not lost, don't care, or "-", add it to the list of specified values.
def calculateValuesSpecified(universe, attrIndex, concept):
    valuesSpecified = set()

    # For each case in the concept, add its value to the list if it is specified
    for case in concept:
        value = universe[case][attrIndex]
        if value != '-' and value != '?' and value != '*':
            valuesSpecified.add(value)
    # Endfor

    return valuesSpecified


# Calculates the cutpoints of the numeric attribute at attribute index attrIndex of the universe
# Returns a list of pairs which the first value is the lower, and the second value is the upper
# of the block.
def calculateCutpointAttrValuePairs(universe, attrIndex):
    values = set()

    # First, store all distinct values and sort them
    for row, case in enumerate(universe):
        value = case[attrIndex]
        if value != '-' and value != '?' and value != '*':
            values.add(float(value))
    # Endfor

    # Sort the set of values (at the same time, convert to list)
    values = sorted(values, key = float)

    numericAttrValuePairs = []
    low = values[0]
    high = values[-1]

    # Find the averages of values and make the two blocks (low to cutpoint, and cutpoint to high)
    for index in range(0, len(values) - 1):
        cutpoint = round(((float(values[index]) + float(values[index + 1])) / 2), 6)
        numericAttrValuePairs.extend([[low, cutpoint], [cutpoint, high]])

    return numericAttrValuePairs

def pairBlockSeparated(attrValueDict, attribute):
    attrValuePairs = []
    attrValueBlocks = []

    for key, value in attrValueDict.items():
        attrValuePairs.append("({}, {})".format(attribute, key))
        attrValueBlocks.append(value)
    # Endfor

    #attrValueBlocks.sort()

    return [attrValuePairs, attrValueBlocks]

def calculateAVBlocks(universe, attrIndex, attrType, attribute, concepts):
    attrValueDict = collections.OrderedDict()

    # If we have a numeric attribute, find the cutpoints and initialize the dictionary
    if attrType == 2:
        # First, calculate the cutpoints and sort them
        cutpointAttrValuePairs = calculateCutpointAttrValuePairs(universe, attrIndex)

        if DEBUG:
            print("Cutpoints calculated for attribute [{}]".format(attribute))

        for interval in cutpointAttrValuePairs:
            intervalString = "{}..{}".format(interval[0], interval[1])
            attrValueDict[intervalString] = set()
        # Endfor
    # Endif

    attrConceptVals = []
    dontCareVals = []

    # For every value, if it isn't incomplete, add it to every block it belongs in
    for row, case in enumerate(universe):
        value = case[attrIndex]

        # If don't care case, add to all existing blocks
        if value == "*":
            dontCareVals.append(row)
        # If attribute-concept case, come back to them at the end
        elif value == "-":
            attrConceptVals.append(row)
        # If lost value, move on
        elif value == "?":
            continue
        # Add this case to the interval setup from cutpoints
        else:
            # If the attribute is numeric, add it to all intervals it belongs to
            if attrType == 2:
                value = float(value)

                # Check every interval to see if this value is in range
                for interval in cutpointAttrValuePairs:
                    if value >= interval[0] and value <= interval[1]:
                        attrValueDict["{}..{}".format(interval[0], interval[1])].add(row)
                # Endfor
            # If this symbolic attribute exists in the dictionary, add the case number
            elif value in attrValueDict:
                attrValueDict[value].add(row)
            # Else, add the newly seen symbolic value as a key in the block table
            else:
                attrValueDict[value] = set([row])
        # Endif
    # Endfor

    # If we're dealing with incomplete data, handle those cases here
    if incompleteDataset:
        # Add all attribute concepts values to blocks which are specified in the concept
        for case in attrConceptVals:
            decision = universe[case][-1]
            attrConcept = calculateValuesSpecified(universe, attrIndex, concepts[decision])
            # For every specified case, add this value to the intervals it was added to
            for item in attrConcept:
                # If the attribute is numeric, add it to all intervals it belongs to
                if attrType == 2:
                    itemVal = float(item)
                    for interval in cutpointAttrValuePairs:
                        if itemVal >= interval[0] and itemVal <= interval[1]:
                            attrValueDict["{}..{}".format(interval[0], interval[1])].add(case)
                    # Endfor
                else:
                    attrValueDict[item].add(case)
            # Endfor
        # Endfor

        # Add all don't care values to every block
        for item in attrValueDict.values():
            item.update(dontCareVals)
    # Endif

    # Convert the dictionary to two lists: attribute value pairs and attribute value blocks
    # return pairBlockSeparated(attrValueDict, attribute)
    return attrValueDict

# Calculates the approximations of the concepts within the universe
def calculateApprox(sets, concepts, approxType):
    approximations = []

    for concept in concepts.values():
        approximations.append(set())
        currentSets = []

        # If the dataset is incomplete, use concept approximations (only take from concept cases)
        if incompleteDataset:
            for number in concept:
                currentSets.append(sets[number])
            # Endfor
        else:
            currentSets = sets

        for block in currentSets:
            if approxType == "lower":
                if block.issubset(concept):
                    approximations[-1].update(block)
            elif not block.isdisjoint(concept):
                approximations[-1].update(block)
        # Endfor
    # Endfor

    for index, approx in enumerate(approximations):
        approximations[index] = sorted(approx, key = int)

    if DEBUG:
        print("Calculated approximations:")
        listPrint(approximations)

    return approximations

def calculateCSets(universe, attrValueDict, attributes, attrTypes, concepts):
    characteristicSets = []

    for index, case in enumerate(universe):
        runningResult = set()

        # For every attribute in the case (not the decision)
        for i in range(0, len(case) - 1):
            value = case[i]
            currentResult = set()

            # Don't care and lost cases equate to the universe in this function
            if value == '*' or value == '?':
                continue
            # Symbolic values
            elif attrTypes[i] == 1:
                # Attribute concept cases 
                if value == '-':
                    valuesSpecified = calculateValuesSpecified(universe, i, concepts[case[-1]])
                    for temp in valuesSpecified:
                        for key, specifiedSet in attrValueDict[attributes[i]].items():
                            currentResult.update(specifiedSet)
                        # Endfor
                    # Endfor
                else:
                    currentResult = attrValueDict[attributes[i]][value]
            # Numeric values
            elif value == '-':
                valuesSpecified = calculateValuesSpecified(universe, i, concepts[case[-1]])
                for temp in valuesSpecified:
                    for key, intervalSet in attrValueDict[attributes[i]].items():
                        interval = key.split("..")
                        map(float, interval)

                        if temp >= interval[0] and temp <= interval[1]:
                            currentResult.update(intervalSet)
                        # Endif
                    # Endfor
                # Endfor
            else:
                value = float(value)
                for key, intervalSet in attrValueDict[attributes[i]].items():
                    interval = key.split("..")
                    interval = [float(i) for i in interval]

                    if value >= interval[0] and value <= interval[1]:
                        currentResult.update(intervalSet)
                    # Endif
                # Endfor
            # Endif

            # If this is the first intersecting set, make it the running result
            if len(runningResult) == 0:
                runningResult = currentResult
            elif len(currentResult) > 0:
                runningResult = set.intersection(runningResult, currentResult)
        # Endfor
        if len(runningResult) == 0:
            print("Error, characteristic set is empty.")
        else:
            characteristicSets.append(runningResult)
    # Endfor

    if DEBUG:
        print("Characteristic sets:")
        for index, cSet in enumerate(characteristicSets):
            print("{}. {}".format(index + 1, cSet))

    return characteristicSets

def equivalentCases(case, caseOther):
    for i in range(0, len(case) - 1):
        if case[i] != caseOther[i]:
            return False
        # Endif
    # Endfor

    return True

# Calculates A* for the given universe. This function parses each case to determine duplicate
# cases, when a duplicate is found (all attribute values match that of another case or cases), it
# is added to the set of cases which share all the same attributes
def calculateAStar(universe):
    aStar = []

    # For every case in the universe, check if it equals an already seen set
    for row, case in enumerate(universe):
        exists = False

        # For every exisitng A* set, check if this case matches one defined
        # If so, add it to that A* subset and breakout
        for aSet in aStar:
            if equivalentCases(case, universe[aSet[0]]):
                aSet.append(row)
                exists = True
                break
            # Endif
        # Endfor

        if not exists:
            aStar.append([row])
    # Endfor

    # Convert them to sets
    for index, aSet in enumerate(aStar):
        aStar[index] = set(aSet)

    return aStar

# The function is responsible for taking input attribute value pairs/block and a set of goals in
# order to determine a set of rules for this dataset. No matter the specification of possible or
# certain rules, this will produce the desired output given the correct blocks and goals.
def mlem2(attrValueDict, goals):
    print("Calculating goals:")
    listPrint(goals)

    return []

# Calculates the set of rules based off of user input
# Choice 1: Calculates the set of certain rules
# Choice 2: Calculates the set of possible rules
# Returns the set of rules that were calculated given the user input choice
def calculateRules(universe, attributes):
    choice = getRuleType()

    # Determine what types the attributes are
    concepts = calculateConcepts(universe)

    # Print out the calculated concepts
    if DEBUG:
        print("Concepts:")
        for key, value in concepts.items():
            print("{}\t: {}".format(key, value))
        print()
    # Endif

    attrTypes = attributeTypes(universe, attributes)
    attrValueDict = collections.OrderedDict()

    # Generate the attribute value pairs and their blocks for both attribute types
    for index, attrType in enumerate(attrTypes):
        attrValueDict[attributes[index]] = calculateAVBlocks(universe, index, attrType, attributes[index], concepts)
    # Endfor

    # Print out the generated attribute value pairs
    if DEBUG:
        print(attrValueDict)

    # Calculate the goals for this query (certain vs. possible inside incomplete vs. complete)
    if not incompleteDataset:
        aStar = calculateAStar(universe)

        if choice == 1:
            goals = calculateApprox(aStar, concepts, "lower")
        else:
            goals = calculateApprox(aStar, concepts, "upper")
    else:
        characteristicSets = calculateCSets(universe, attrValueDict, attributes, attrTypes, concepts)

        if choice == 1:
            goals = calculateApprox(characteristicSets, concepts, "lower")
        else:
            goals = calculateApprox(characteristicSets, concepts, "upper")

    # Return the calculation of the rules using mlem2
    return mlem2(attrValueDict, goals)

# Prints the output ruleSet to a filename given by the user
def printOutput(ruleSet):
    outputFileName = input("What is the name of the output file?\t\t")
    print("\nOutput file accepted: [{}]\n".format(outputFileName)) 
    outputFile = open(outputFileName, "w")

    for rule in ruleSet:
        outputFile.write("%s\n" % rule)

    # DEBUG print the ruleset generated at the very end
    if DEBUG:
        listPrint(ruleSet)

    print("Ruleset exported to output file [{}].\n".format(outputFileName))

# The main function of the MLEM2 algorithm program
# Accepts an inputFileName from the user to parse. Checks if the file can be opened, if so, prompts the
# user for a calculation method (certain vs possible rulesets). Finally, computes the rulesets
# using the MLEM2 algorithm.
#
# Handles numerical attribute values using the all cutoffs approach
# Handles missing attribute values using concept approximations
def main():
    print("-------------------------------------------------------------") 
    print("|              Welcome to Jay's MLEM2 Program!              |")
    print("|                                                           |")
    print("|              EECS690 - Data Mining Fall 2016              |")
    print("-------------------------------------------------------------") 
    
    # Store all of the input data in the attributes/universe structures
    attributes = []
    universe = parseFile(attributes)
    print("-------------------------------------------------------------\n")

    # Calculate the rulesets from the universe/attributes
    ruleSet = calculateRules(universe, attributes)
    print("-------------------------------------------------------------\n")

    # Print the output to the desired file
    printOutput(ruleSet)

main()
