###################################################################################################
#
#   Program: Rule Induction with MLEM2
#   Author: Jay Offerdahl
#   Class: EECS690 (Dr. Grzymala-Busse), Fall 2016
#
#   Description: Prompts the user for input/output files as well as a choice between calculating
#                certain or possible rules. The program parses the input file and performs some
#                amount of preprocessing before inducing the rules using the MLEM2 algorithm.
#                After the rules have been induced, the program asks the user if they want to also
#                calculate the other set of rules in order to save a large amount of preprocessing.
#
###################################################################################################

from collections import OrderedDict
import re
import sys
import time

__inputFile__ = None
__inputFileName__ = ""
__outputFile__ = None
__outputFileName__ = ""
__calcCertain__ = False
__incompleteDataset__ = False

# Output flags --> set to 1 if output is desired
DEBUG = 0
FASTRULES = 0
STATUSINFO = 1

# Prints out an enumerable object token by token, separating tokens with a newline.
# Will print lines with link numbers starting at 0 if PRINT_LINE_NUMBERS is True
def listPrint(lst):
    if not lst: print("[]")
    for token in lst: print(token)
    print()

# Prompts the user for valid input until the input filename can be opened.
def checkFile(fileName):
    while True:
        try:
            file = open(fileName)
            break
        except IOError:
            fileName = input("Error, the file could not be opened. Try again:\t\t")
    file.close()

    if STATUSINFO:
        print("\nFile accepted: [{}]".format(fileName))
    print()
    return fileName

# Prompts the user for the input/output filenames and checks if they're valid, also gets rule type
def userInput():
    global __inputFileName__
    __inputFileName__ = checkFile(input("\nWhat is the name of the input dataset file?\t"))

    # Ask the user what type of rules (certain or possible) they want to generate.
    getRuleType()

    global __outputFileName__
    __outputFileName__ = checkFile(input("What is the name of the output file?\t\t"))

# Parses the input file and stores all relevant information for parsing.
# Modifies the array of cases to include the universe of cases
#   Each case has a list of indicies to a dictionary key which specifies the value of the attribute
# Modifies the dictionary of attributes to include all attributes values seen
def parseFile(attributes):
    global __incompleteDataset__

    inputFile = open(__inputFileName__)

    # Parse the input file to generate the universe of cases
    skipInput = True
    readAttrs = False
    universe = []
    currentCase = []
    attr = 0

    # Skip the < a ... a d > descriptors, read in attribute names/decision name
    for line in inputFile:
        tokens = line.split()

        for token in tokens:
            # If a comment is encountered, skip the rest of the line
            if token == '!':
                break
            # Adjust flags to now accept attribute names
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
                        # Duplicate token, invalid dataset.
                        print("Error [Invalid dataset]: Token already recognized.\n")
                        sys.exit()
            elif not skipInput and not readAttrs:
                # Check here if there are any missing attributes (must check all tokens)
                if not __incompleteDataset__ and (token == '?' or token == '*' or token == '-'):
                    __incompleteDataset__ = True

                if attr >= len(attributes):
                    # Finished a case, reset attribute counter and append this list to the universe
                    attr = 0
                    universe.append(currentCase)
                    currentCase = []

                currentCase.append(token)
                attr += 1
    # Append the last currentCase (last line)
    universe.append(currentCase)

    if STATUSINFO:
        print("Input file parsed. There are {} total cases.".format(len(universe)))
        if __incompleteDataset__:
            print("  **This dataset is incomplete; using concept approximations.\n")

    return universe

# Captures user input to determine which rule type to calculate
# Choice 1: Calculates the set of certain rules
# Choice 2: Calculates the set of possible rules
# Returns the choice of the user
def getRuleType():
    print("What do you want to calculate?\n  1. Certain Rules\n  2. Possible Rules\n")

    # While invalid input from the user (out of bounds or of wrong type)
    while True:
        try:
            choice = int(input("Choice: "))
            if 1 <= choice <= 2:
                break
        except ValueError:
            print("Please enter a number.")
    rule = "certain" if choice == 1 else "possible"

    if STATUSINFO:
        print("\nChoice {} accepted; calculating {} rules from input data.\n".format(choice, rule))

    global __calcCertain__
    __calcCertain__ = choice == 1

# Prompt the user to determine if the other ruleset should be calculated. For example, if the user
# originally requested certain rules, a "y" here means they also want to calculate possible rules.
def calculateOtherSet():
    rulesOther = "possible" if __calcCertain__ else "certain"
    calculateOtherSet = input("Calculate {} rules as well? (y/n) ".format(rulesOther))
    print()

    # If yes, back out and calculate
    if calculateOtherSet == 'y' or calculateOtherSet == 'Y':
        global __outputFileName__
        __outputFileName__ = checkFile(input("What is the name of the output file?\t\t"))
        return True
    return False

# Determine what type each attribute belongs to
# Type 1: Symbolic
# Type 2: Numeric
# Type 3: Missing (A type 3 attribute confirms invalid input and exits the program)
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
                print("Error [Invalid dataset]: type 3 attribute.\n")
                sys.exit()

    if STATUSINFO:
        print("Attribute types evaluated. There are {} attributes.".format(len(attributes) - 1))
        print("  **{} symbolic attributes, {} numeric attributes.\n".format(type1, type2))

    return types

# Computes the concepts for the given universe (sets of distinct cases with the same decision)
def calculateConcepts(universe):
    concepts = OrderedDict()

    # For every case in the universe, add the case number to the concept set it belongs
    for index, case in enumerate(universe):
        decision = case[-1]

        if decision in concepts:
            concepts[decision].add(index)
        else:
            concepts[decision] = set([index])

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

    return valuesSpecified

# Calculates the cutpoints of the numeric attribute at attribute index attrIndex of the universe
# Returns a list of pairs: index 0 is the lower bound, index 1 is the upper bound of the interval
def calculateCutpointAttrValuePairs(universe, attrIndex):
    values = set()

    # First, store all distinct values and sort them
    for row, case in enumerate(universe):
        value = case[attrIndex]
        if value != '-' and value != '?' and value != '*':
            values.add(float(value))

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

    return [attrValuePairs, attrValueBlocks]

def generateAVBlocks(universe, attrIndex, attrType, attribute, concepts):
    attrValueDict = OrderedDict()

    # If we have a numeric attribute, find the cutpoints and initialize the dictionary
    if attrType == 2:
        cutpointAttrValuePairs = calculateCutpointAttrValuePairs(universe, attrIndex)

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
            # If the attribute is numeric, add it to all intervals it belongs to
            if attrType == 2:
                value = float(value)

                # Check every interval to see if this value is in range
                for interval in cutpointAttrValuePairs:
                    if value >= interval[0] and value <= interval[1]:
                        attrValueDict["{}..{}".format(interval[0], interval[1])].add(row)
            # If this symbolic attribute exists in the dictionary, add the case number
            elif value in attrValueDict:
                attrValueDict[value].add(row)
            # Else, add the newly seen symbolic value as a key in the block table
            else:
                attrValueDict[value] = set([row])

    # If we're dealing with incomplete data, handle those cases here
    if __incompleteDataset__:
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
                else:
                    attrValueDict[item].add(case)
        # Add all don't care values to every block
        for item in attrValueDict.values():
            item.update(dontCareVals)

    return attrValueDict

# Calculates the approximations of the concepts within the universe
def calculateApprox(sets, concepts, approxType):
    approximations = OrderedDict()

    for decision, concept in concepts.items():
        approximations[decision] = set()
        currentSets = []

        # If the dataset is incomplete, use concept approximations (only take from concept cases)
        if __incompleteDataset__:
            for number in concept:
                currentSets.append(sets[number])
        else:
            currentSets = sets

        for block in currentSets:
            if approxType == "lower":
                if block.issubset(concept):
                    approximations[decision].update(block)
            elif not block.isdisjoint(concept):
                approximations[decision].update(block)
    return approximations

def generateFloatInterval(interval):
    edges = interval.split("..")
    return [float(i) for i in edges]

def calculateCSets(universe, attrValueDict, attributes, attrTypes, concepts):
    characteristicSets = []

    for case in universe:
        runningResult = set()

        # For every attribute
        for i in range(0, len(attributes) - 1):
            value = case[i]
            currentResult = set()

            # Don't care and lost cases equate to the universe in this function
            if value == '*' or value == '?':
                continue
            # Attribute concept values
            elif value == '-':
                valuesSpecified = calculateValuesSpecified(universe, i, concepts[case[-1]])
                for temp in valuesSpecified:
                    for key, tempSet in attrValueDict[attributes[i]].items():
                        if attrTypes[i] == 1:
                            if temp == key:
                                currentResult.update(tempSet)
                        else:
                            temp = float(temp)
                            edges = generateFloatInterval(key)

                            if edges[0] <= temp <= edges[1]:
                                currentResult.update(tempSet)
            # Symbolic values
            elif attrTypes[i] == 1:
                currentResult = attrValueDict[attributes[i]][value]
            else:
                value = float(value)

                # Calculate the "common area" for this
                for key, intervalSet in attrValueDict[attributes[i]].items():
                    edges = generateFloatInterval(key)

                    # If this value is in range of this interval, see if we can tighten with it
                    if edges[0] <= value <= edges[1]:
                        currentResult.update(intervalSet)
            # If this is the first intersecting set, make it the running result
            if not runningResult:
                runningResult = currentResult
            elif currentResult:
                runningResult = set.intersection(runningResult, currentResult)
        if not runningResult:
            print("Error, characteristic set is empty.")
        else:
            characteristicSets.append(runningResult)
    return characteristicSets

# Determine if the two input cases have all equivalent attributes. Returns false as soon as an
# attribute doesn't match. If all attributes are checked without failure, return true.
def equivalentCases(case, caseOther):
    for i in range(0, len(case) - 1):
        if case[i] != caseOther[i]:
            return False
    return True

# Calculates A* for the given universe. This function parses each case to determine duplicate
# cases, when a duplicate is found (all attribute values match that of another case or cases), it
# is added to the set of cases which share all the same attributes
def calculateAStar(universe):
    aStar = []

    # For every case in the universe, check if it equals an already seen set
    for row, case in enumerate(universe):
        exists = False

        # For every exisitng A* set, check if this case matches a defined one (Add it if it does)
        for aSet in aStar:
            if equivalentCases(case, universe[aSet[0]]):
                aSet.append(row)
                exists = True
                break
        if not exists:
            aStar.append([row])
    # Convert them to sets
    for index, aSet in enumerate(aStar):
        aStar[index] = set(aSet)

    return aStar

# The function is responsible for taking input attribute value pairs/block and a set of goals in
# order to determine a set of rules for this dataset. No matter the specification of possible or
# certain rules, this will produce the desired output given the correct blocks and goals.
def mlem2(attrValueDict, attrTypes, goals, attrDecision):
    if STATUSINFO:
        print("-------------------------------------------------------------\n")
        print("Rule induction commencing for calculated goals:")
        listPrint(goals.items())

    ruleSet = []

    # For every concept we're evaluating
    for decision, originalGoal in goals.items():
        goal = set(originalGoal)
        goalSize = len(goal)
        goalCompleted = 0
        remainingGoal = goal
        runningBlock = set()
        rules = OrderedDict()

        if goal and STATUSINFO:
            print("Calculating rules for [{}]".format(decision))
            print("\r{}%\t[".format(round(goalCompleted / goalSize * 100), 1), end = "", flush = True)
            for i in range(59):
                print(" ", end = "", flush = True)
            print("]", end = "", flush = True)

        # While we haven't found a covering
        while len(goal):
            # Find the intersection in the following priority scheme:
            #   - Cardinality is maximum
            #   - Smallest cardinality of the block
            #   - First pair seen
            matchedGoal = set()
            selectionBlock = set()

            for index, (attribute, attrValSet) in enumerate(attrValueDict.items()):
                for value, t in attrValSet.items():
                    if ((attrTypes[index] == 1 and attribute not in rules) or
                        attrTypes[index] == 2):
                        update = True
                        temp = t.intersection(goal)
                        if ((len(temp) > len(matchedGoal)) or
                            len(temp) == len(matchedGoal) and len(t) < len(selectionBlock)):
                            if attrTypes[index] == 2:
                                if attribute in rules and value in rules[attribute]:
                                    update = False
                                # We've seen this attribute, tighten the rule
                                elif attribute in rules:
                                    low = "unset"
                                    high = "unset"
                                    # Calculate current interval
                                    for interval in rules[attribute]:
                                        edges = generateFloatInterval(interval)
                                        # First time set
                                        if low == "unset":
                                            low = edges[0]
                                            high = edges[1]
                                        else:
                                            low = edges[0] if edges[0] > low else low
                                            high = edges[1] if edges[1] < high else high

                                    # Check if the intervals overlap, if not, don't use this one
                                    interval = generateFloatInterval(value)

                                    if not (low < interval[0] < high or low < interval[1] < high):
                                        update = False
                            if update:
                                matchedGoal = temp
                                selectionVal = value
                                selectionAttr = attribute
                                selectionBlock = t

            # Update our running block
            if runningBlock:
                runningBlock = runningBlock.intersection(selectionBlock)
            else:
                runningBlock = selectionBlock

            # Append our choice to the rule attributes/values containers
            if selectionAttr in rules:
                rules[selectionAttr].append(selectionVal)
            else:
                rules[selectionAttr] = [selectionVal]

            if DEBUG:
                print("Selecting ({}, {}) : {}".format(selectionAttr, selectionVal, selectionBlock))
                print("Selecting ({}, {})".format(selectionAttr, selectionVal))

            # If we can make a rule, add it to the ruleset and update the goal to be what's missing
            if len(runningBlock) and runningBlock.issubset(originalGoal):
                if DEBUG:
                    print("Attempting rule simplification for {}".format(rules))
                # Combine numerical intervals to form the smallest interval (and save the
                # calculated interval sets for condition dropping below
                for key, value in rules.items():
                    # If the length > 1, it's a numeric value that needs combining
                    if len(value) > 1:
                        low = None
                        high = None
                        intervalValues = set()

                        # Calculate the "common area" for these conditions
                        for interval in rules[key]:
                            tempSet = attrValueDict[key][interval]
                            edges = generateFloatInterval(interval)
                            if low == None:
                                low, high = edges
                                intervalValues = tempSet
                            # Else, we'll only ever update one side at a time
                            else:
                                low = edges[0] if edges[0] > low else low
                                high = edges[1] if edges[1] < high else high

                                # Update the values to the tightest interval we have found
                                intervalValues = intervalValues.intersection(tempSet)
                        # Add this interval set to the attrValueDict for condition dropping
                        newInterval = "{}..{}".format(low, high)
                        if newInterval not in attrValueDict[key]:
                            attrValueDict[key][newInterval] = intervalValues

                        rules[key] = [newInterval]

                # Condition dropping --> if we can do without a condition, drop it
                for attribute in list(rules):
                    testBlock = set()
                    # Find the intersection without this value
                    for testAttr, testVal in rules.items():
                        block = attrValueDict[testAttr][testVal[0]]
                        if testVal != rules[attribute]:
                            if testBlock:
                                testBlock = testBlock.intersection(block)
                            else:
                                testBlock = block

                    if len(testBlock) and testBlock.issubset(originalGoal):
                        rules.pop(attribute, None)

                # After condition dropping, compute the final test block to remove from
                # the remaining goal (a.k.a. hardest bug to find ever)
                matchedSet = set()
                for attribute, key in rules.items():
                    if DEBUG:
                        print("{}:{}".format(attribute, key))
                    block = attrValueDict[attribute][key[0]]
                    if DEBUG:
                        print(block)
                    if len(matchedSet):
                        matchedSet = matchedSet.intersection(block)
                    else:
                        matchedSet = block
                    if DEBUG:
                        print(matchedSet)
                        print()

                if STATUSINFO:
                    newMatches = remainingGoal.intersection(matchedSet)
                    goalCompleted += len(newMatches)
                    print("\r{}%\t[".format(round(goalCompleted / goalSize * 100), 1), end = "", flush = True)
                    calc = int(goalCompleted / goalSize * 59)
                    for i in range(calc):
                        print("=", end = "", flush = True)
                    for i in range(59 - calc):
                        print(" ", end = "", flush = True)
                    print("]", end = "", flush = True)

                remainingGoal = remainingGoal - matchedSet
                goal = goal - matchedSet

                if DEBUG:
                    print("We actually matched {}".format(matchedSet))
                    print(rules)

                if DEBUG:
                    print("Matched {}, remaining: {}".format(runningBlock, remainingGoal))
                    print("New values matched here:,",matchedGoal)
                if not len(goal):
                    goal = remainingGoal
                    if DEBUG:
                        if not len(remainingGoal):
                            print("***Original goal covered!***:")
                        else:
                            print("***Partially covered original goal, continuing***")
                        print()
                elif DEBUG:
                    print("Current goal update:",goal)

                # Add the new rule (with dropped values) to the ruleset
                if FASTRULES:
                    print(makeFriendlyRules([[rules, [attrDecision, decision]]]))
                ruleSet.append([rules, [attrDecision,  decision]])
                rules = OrderedDict()
                numericRuleVals = dict()
                runningBlock = set()
            else:
                goal = matchedGoal

        if STATUSINFO:
            print("\n")

    # Convert the induced rules to a friendly format and output them
    printOutput(makeFriendlyRules(ruleSet))

# Converts a given ruleset containing a list of attributes and values as well as decision values
# into a friendly rule format matching (attr, value) & ... & (attr, value) -> (d, decision)
def makeFriendlyRules(ruleSet):
    friends = []

    # Generate a friendly formatted rule for each rule in the ruleSet
    for rule in ruleSet:
        friendlyRule = ""
        for index, (attribute, value) in enumerate(rule[0].items()):
            if index != 0:
                friendlyRule +=" & "
            friendlyRule += "({}, {})".format(attribute, value[0])
        friendlyRule += " -> ({}, {})".format(rule[1][0], rule[1][1])

        friends.append(friendlyRule)

    return friends

# Calculates the set of rules using calculated approximations and the MLEM2 algorithm
def calculateRules(universe, attributes, attrValueDict, attrTypes, concepts):
    # Generate the corresponding sets (A* if complete, characteristic sets if not complete)
    if not __incompleteDataset__:
        sets = calculateAStar(universe)
    else:
        sets = calculateCSets(universe, attrValueDict, attributes, attrTypes, concepts)

    global __calcCertain__
    approxType = "lower" if __calcCertain__ else "upper"
    goals = calculateApprox(sets, concepts, approxType)
    mlem2(attrValueDict, attrTypes, goals, attributes[-1])

    # Ask the user if they want to calculate the other set of rules (certain or possible)
    if calculateOtherSet():
        approxType = "upper" if __calcCertain__ else "lower"
        goals = calculateApprox(sets, concepts, approxType)
        __calcCertain__ = not __calcCertain__
        mlem2(attrValueDict, attrTypes, goals, attributes[-1])

# Prints the output ruleSet to a filename given by the user
def printOutput(ruleSet):
    if STATUSINFO:
        ruleStr = "Certain" if __calcCertain__ else "Possible"
        print("{} rules have been induced:".format(ruleStr))
        if not ruleSet:
            print("  **No rules were produced of this type.\n")
        else:
            listPrint(ruleSet)

    outputFile = open(__outputFileName__, "w")

    for rule in ruleSet:
        outputFile.write("%s\n" % rule)

    if STATUSINFO: print("Rules exported successfully.\n".format(__outputFileName__))

# The main function of the MLEM2 algorithm program
# Accepts an __inputFileName__ from the user to parse. Prompts user for a type of ruleset to compute
# (certain rules vs. possible rules). Finally, computes the rulesets using the MLEM2 algorithm.
#
# Handles numerical attribute values using the all cutoffs approach
# Handles missing attribute values using concept approximations
def main():
    print("-------------------------------------------------------------")
    print("|              Welcome to Jay's MLEM2 Program!              |")
    print("|                                                           |")
    print("|              EECS690 - Data Mining Fall 2016              |")
    print("-------------------------------------------------------------")

    # Ask the user for input/output file names and rule types to calculate
    userInput()

    attributes = []
    universe = parseFile(attributes)

    # Store the concepts of this dataset
    concepts = calculateConcepts(universe)

    #Determine what types the attributes are
    attrTypes = attributeTypes(universe, attributes)
    attrValueDict = OrderedDict()

    # Generate the attribute value pairs and their blocks
    for index, attrType in enumerate(attrTypes):
        attribute = attributes[index]
        attrValueDict[attribute] = generateAVBlocks(universe, index, attrType, attribute, concepts)

    # Calculate the rulesets from the universe/attributes
    calculateRules(universe, attributes, attrValueDict, attrTypes, concepts)

main()
