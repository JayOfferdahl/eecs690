import re
import sys
import time
import collections

inputFileName = ""
outputFileName = ""
incompleteDataset = False
DEBUG = 0
PRINT_LINE_NUMBERS = 0

# Prints out a list token by token, separating tokens with a newline
def listPrint(list):
    for index, token in enumerate(list):
        if PRINT_LINE_NUMBERS:
            print("{} ".format(index), end = "", flush = True)
        print(token)

    # Finish with a 1 line spacer
    print()

# Spin up intelliJ
def spinUpIntelliJ():
    print("Spinning up IntelliJ", end = "", flush = True)
    for i in range(0, 24):
        print(".", end = "", flush = True)
        time.sleep(.05)
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

                # TODO --> check for numerical attributes here
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

    # return the dictionary
    return universe

# Captures user input to determine which rule type to calculate
# Choice 1: Calculates the set of certain rules
# Choice 2: Calculates the set of possible rules
# Returns the choice of the user
def getRuleType():
    print("What do you want to calculate?\n   1. Certain Rules\n   2. Possible Rules\n")

    while True:
        try:
            choice = int(input("Choice: "))

            if choice >= 1 and choice <= 2:
                break
        except ValueError:
            print("Please enter a number.")

    print("\nChoice {} accepted.\n".format(choice))

    if choice == 1:
        print("Calculating certain rules from dataset: [{}]\n".format(inputFileName))
    else:
        print("Calculating possible rules from dataset: [{}]\n".format(inputFileName))

# Computes the concepts for the given universe (sets of distinct cases with the same decision)
def calculateConcepts(universe):
    concepts = dict()

    for index, case in enumerate(universe):
        decision = case[-1]

        if decision in concepts:
            concepts[decision].add(index)
        else:
            concepts[decision] = set([index])
    # Endfor

    return concepts

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

            # Uses regex to figure out what type we're dealing with
            match = re.fullmatch(decimal + "\.\." + decimal, attr)
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
    
    if DEBUG:
        for i in range(0, len(types)):
            print("{}:{}".format(attributes[i], types[i]))
        print()

    return types

# Computes the specified values for the given concept. If a value for the given attribute index
# is not lost, don't care, or "-", add it to the list of specified values.
def calculateValuesSpecified(universe, attrIndex, concept):
    valuesSpecified = []

    # For each case in the concept, see if a value is specified, if so, add it to the list
    for case in concept:
        value = universe[case][attrIndex]
        if value != '-' and value != '?' and value != '*':
            valuesSpecified.append(value)
    # Endfor

    return valuesSpecified

def pairBlockSeparated(attrValueDict, attribute):
    attrValuePairs = []
    attrValueBlocks = []

    for key, value in attrValueDict.items():
        attrValuePairs.append("({}, {})".format(attribute, key))
        attrValueBlocks.append(value)

    attrValueBlocks.sort()

    return [attrValuePairs, attrValueBlocks]

# Calculates the attribute value blocks for the given attribute in the universe
def calculateSymbolicAVBlocks(universe, attrIndex, attribute, concepts):
    attrValueDict = dict()
    attrConceptVals = []
    dontCareVals = []

    # For every new symbol we see, add a pair for it
    # If we've seen the symbol before, add this case to the block
    for row, case in enumerate(universe):
        value = case[attrIndex]

        # If don't care case, add to all existing blocks at the end
        if value == "*":
            dontCareVals.append(row)
        # If attribute-concept case, come back to them at the end
        elif value == "-":
            attrConceptVals.append(row)
        # If the case exists, add this row (case number) to the block
        elif value in attrValueDict:
            attrValueDict[value].add(row)
        # Else, create a new key in the block table
        else:
            attrValueDict[value] = set([row])
    # Endfor

    # Add all attribute concepts values to blocks which are specified in the concept
    for case in attrConceptVals:
        decision = universe[case][-1]
        attrConcept = calculateValuesSpecified(universe, attrIndex, concepts[decision])
        for item in attrConcept:
            attrValueDict[item].add(case)
    # Endfor

    # Add all don't care cases to every symbol seen
    for case in dontCareVals:
        for item in attrValueDict.values():
            item.add(case)

    # Convert the dictionary to two lists: attribute value pairs and attribute value blocks
    return pairBlockSeparated(attrValueDict, attribute)

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

    cutpoints = []

    # Find the averages of values and make the two blocks (low to cutpoint, and cutpoint to high)
    for index in range(0, len(values) - 1):
        cutpoint = (float(values[index]) + float(values[index + 1])) / 2
        cutpoints.append(cutpoint)

    numericAttrValuePairs = []
    low = values[0]
    high = values[-1]

    # Now that we have the cutpoints, make all necessary blocks
    for cutpoint in cutpoints:
        numericAttrValuePairs.append([low, cutpoint])
        numericAttrValuePairs.append([cutpoint, high])

    return numericAttrValuePairs

def calculateNumericAVBlocks(universe, attrIndex, attribute, concepts):
    # First, calculate the cutpoints and sort them
    cutpointAttrValuePairs = calculateCutpointAttrValuePairs(universe, attrIndex)

    print("Cutpoints calculated for attribute [{}]".format(attribute))

    attrValueDict = collections.OrderedDict()

    for interval in cutpointAttrValuePairs:
        intervalString = "{}..{}".format(interval[0], interval[1])
        attrValueDict[intervalString] = set()

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
            value = float(value)

            # Check every interval to see if this value is in range
            for interval in cutpointAttrValuePairs:
                if value >= interval[0] and value <= interval[1]:
                    attrValueDict["{}..{}".format(interval[0], interval[1])].add(row)
            # Endfor
        # Endif
    # Endfor

    # Add all attribute concepts values to blocks which are specified in the concept
    for row in attrConceptVals:
        decision = universe[row][-1]
        attrConcept = calculateValuesSpecified(universe, attrIndex, concepts[decision])
        # For every specified case, add this value to the intervals it was added to
        for item in attrConcept:
            itemVal = float(item)
            for interval in cutpointAttrValuePairs:
                if itemVal >= interval[0] and itemVal <= interval[1]:
                    attrValueDict["{}..{}".format(interval[0], interval[1])].add(row)
            # Endfor
        # Endfor
    # Endfor

    # Add all don't care values to every block
    for case in dontCareVals:
        for item in attrValueDict.values():
            item.add(case)

    # Convert the dictionary to two lists: attribute value pairs and attribute value blocks
    return pairBlockSeparated(attrValueDict, attribute)

# Searches for the concept to which this case belongs by querying all exisiting concepts
def findConceptByCase(concepts, index):
    for concept in concepts.values():
        if index in concept:
            return concept
        # Endif
    # Endfor

    print("Error, concept not found for case number:", index)
    return []

# Calculates the set of rules based off of user input
# Choice 1: Calculates the set of certain rules
# Choice 2: Calculates the set of possible rules
# Returns the set of rules that were calculated given the user input choice
def calculateRules(universe, attributes):
    choice = getRuleType()

    # Determine what types the attributes are
    concepts = calculateConcepts(universe)
    print("Concepts:")
    for key, value in concepts.items():
        print("{} : {}".format(key, value))
    print()
    attrTypes = attributeTypes(universe, attributes)
    attrValuePairs = []
    attrValueBlocks = []

    # Generate the attribute value pairs and their blocks for both attribute types
    for index, attrType in enumerate(attrTypes):
        # For each attribute, if it's numeric type, calculate the cutpoints
        if attrType == 2:
            tempPairs = calculateNumericAVBlocks(universe, index, attributes[index], concepts)
        # If it's symbolic type, add a pair for each value seen
        else:
            tempPairs = calculateSymbolicAVBlocks(universe, index, attributes[index], concepts)

        for pair in tempPairs[0]:
            attrValuePairs.append(pair)
        for block in tempPairs[1]:
            attrValueBlocks.append(block)
    # Endfor

    # Print out the generated attribute value pairs
    if DEBUG:
        listPrint(attrValuePairs)
        listPrint(attrValueBlocks)

    rules = attributes

    return rules

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
