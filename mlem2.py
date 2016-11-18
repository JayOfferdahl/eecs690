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

import collections
import re
import sys
import time

__inputFile__ = ""
__calcCertain__ = False
__incompleteDataset__ = False
lowerApproximations = None

# Debug flag, if set to 0, all debugging statements will be silenced
DEBUG = 0

# Prints out an enumerable object token by token, separating tokens with a newline.
# Will print lines with link numbers starting at 0 if PRINT_LINE_NUMBERS is True
def listPrint(lst):
    if not lst: print("[]")
    for token in lst: print(token)
    print()

# Parses the input file and stores all relevant information for parsing.
# Modifies the array of cases to include the universe of cases
#   Each case has a list of indicies to a dictionary key which specifies the value of the attribute
# Modifies the dictionary of attributes to include all attributes values seen
def parseFile(attributes):
    global __inputFile__
    global __incompleteDataset__
    __inputFile__= input("\nWhat is the name of the input dataset file?\t")

    while True:
        try:
            file = open(__inputFile__)
            break
        except IOError:
            __inputFile__ = input("Error, the file could not be opened. Try again:\t\t")
    # Endwhile

    print("\nInput file accepted: [{}]\n".format(__inputFile__))

    # Parse the input file to generate the universe of cases
    skipInput = True
    readAttrs = False
    universe = []
    currentCase = []
    attr = 0

    # Skip the < a ... a d > descriptors, read in attribute names/decision name
    for line in file:
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
                        print("Error: Token already recognized.\n")
                # Endif
            elif not skipInput and not readAttrs:
                # Check here if there are any missing attributes (must check all tokens)
                if not __incompleteDataset__ and (token == '?' or token == '*' or token == '-'):
                    __incompleteDataset__ = True

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
    universe.append(currentCase)

    print("Input file parsed. There are {} total cases.".format(len(universe)))

    if __incompleteDataset__:
        print("  **This dataset is incomplete; using concept approximations.\n")

    # return the input dataset
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

            if choice >= 1 and choice <= 2:
                break
        except ValueError:
            print("Please enter a number.")
    # Endwhile

    rule = "certain" if choice == 1 else "possible"
    print("\nChoice {} accepted; calculating {} rules from input data.\n".format(choice, rule))

    return choice == 1

# Prompt the user to determine if the other ruleset should be calculated. For example, if the user
# originally requested certain rules, a "y" here means they also want to calculate possible rules.
def calculateOtherSet():
    rulesOther = "possible" if __calcCertain__ else "certain"
    print("-------------------------------------------------------------\n")
    calculateOtherSet = input("Do you want to also calculate {} rules? (y/n)\n\n".format(rulesOther))

    # If yes, back out and calculate
    if calculateOtherSet == 'y' or calculateOtherSet == 'Y':
        return True
    # Else, we're done here
    else:
        sys.exit()

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

    print("Attribute types evaluated. There are {} attributes.".format(len(attributes) - 1))
    print("  **{} symbolic attributes, {} numeric attributes.\n".format(type1, type2))

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

def generateAVBlocks(universe, attrIndex, attrType, attribute, concepts):
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
    approximations = collections.OrderedDict()

    for decision, concept in concepts.items():
        approximations[decision] = set()
        currentSets = []

        # If the dataset is incomplete, use concept approximations (only take from concept cases)
        if __incompleteDataset__:
            for number in concept:
                currentSets.append(sets[number])
            # Endfor
        else:
            currentSets = sets

        for block in currentSets:
            if approxType == "lower":
                if block.issubset(concept):
                    approximations[decision].update(block)
            elif not block.isdisjoint(concept):
                approximations[decision].update(block)
        # Endfor
    # Endfor

    for index, approx in approximations.items():
        approximations[index] = sorted(approx, key = int)

    return approximations

def calculateCSets(universe, attrValueDict, attributes, attrTypes, concepts):
    characteristicSets = []

    for case in universe:
        runningResult = set()

        # For every attribute in the case (not the decision)
        for i in range(0, len(case) - 1):
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
                            interval = key.split("..")
                            map(float, interval)

                            if temp >= interval[0] and temp <= interval[1]:
                                currentResult.update(tempSet)
                        # Endif
                    # Endfor
                # Endfor
            # Symbolic values
            elif attrTypes[i] == 1:
                currentResult = attrValueDict[attributes[i]][value]
            else:
                value = float(value)
                intervalLow = "unset"
                intervalHigh = "unset"
                intervalValues = set()

                # Calculate the "common area" for this
                for key, intervalSet in attrValueDict[attributes[i]].items():
                    interval = key.split("..")
                    interval = [float(i) for i in interval]

                    # If this value is in range of this interval, see if we can tighten with it
                    if value >= interval[0] and value <= interval[1]:
                        # First time set
                        if intervalLow == "unset":
                            intervalLow = interval[0]
                            intervalHigh = interval[1]
                            intervalValues = intervalSet
                        # Else, we'll only ever update one side at a time
                        else:
                            if interval[0] > intervalLow:
                                intervalLow = interval[0]
                            elif interval[1] < intervalHigh:
                                intervalHigh = interval[1]

                            # Update the values to the tightest interval we have found
                            intervalValues = intervalValues.intersection(intervalSet)
                        # Endif
                    # Endif
                # Endfor
                # Our current set is then the values in the tightest possible interval
                currentResult.update(intervalValues)
            # Endif

            # If this is the first intersecting set, make it the running result
            if not runningResult:
                runningResult = currentResult
            elif currentResult:
                runningResult = set.intersection(runningResult, currentResult)
        # Endfor
        if not runningResult:
            print("Error, characteristic set is empty.")
        else:
            characteristicSets.append(runningResult)
    # Endfor

    if DEBUG:
        print("Characteristic sets:")
        for index, cSet in enumerate(characteristicSets):
            print("{}. {}".format(index + 1, cSet))

    return characteristicSets

# Determine if the two input cases have all equivalent attributes. Returns false as soon as an
# attribute doesn't match. If all attributes are checked without failure, return true.
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
def mlem2(attrValueDict, attrTypes, goals, attrDecision):
    print("-------------------------------------------------------------\n")
    print("Rule induction commencing for calculated goals:")
    listPrint(goals.items())

    ruleSet = []

    # For every concept we're evaluating
    for decision, originalGoal in goals.items():
        goal = set(originalGoal)
        remainingGoal = goal
        runningBlock = set()
        rules = collections.OrderedDict()

        # While we haven't found a covering
        while len(goal) > 0:
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
                                if attribute not in rules or value not in rules[attribute]:
                                    update = True
                                else:
                                    update = False
                            if update:
                                matchedGoal = temp
                                selectionVal = value
                                selectionAttr = attribute
                                selectionBlock = t
                        # Endif
                    # Endif
                # Endfor
            # Endfor

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

            # If we can make a rule, add it to the ruleset and update the goal to be what's missing
            if runningBlock.issubset(originalGoal):
                remainingGoal = remainingGoal - runningBlock
                goal = goal - runningBlock

                if not len(goal):
                    goal = remainingGoal


                # Combine numerical intervals to form the smallest interval (and save the
                # calculated interval sets for condition dropping below
                for key, value in rules.items():
                    # If the length > 1, it's a numeric value that needs combining
                    if len(value) > 1:
                        low = "unset"
                        high = "unset"
                        intervalValues = set()

                        # Calculate the "common area" for these conditions
                        for interval in rules[key]:
                            tempSet = attrValueDict[key][interval]
                            edges = interval.split("..")
                            edges = [float(i) for i in edges]
                            # First time set
                            if low == "unset":
                                low = edges[0]
                                high = edges[1]
                                intervalValues = tempSet
                            # Else, we'll only ever update one side at a time
                            else:
                                if edges[0] > low:
                                    low = edges[0]
                                elif edges[1] < high:
                                    high = edges[1]

                                # Update the values to the tightest interval we have found
                                intervalValues = intervalValues.intersection(tempSet)
                            # Endif
                        # Endfor
                        newInterval = "{}..{}".format(low, high)

                        # Add this interval set to the attrValueDict for condition dropping
                        if newInterval not in attrValueDict[key]:
                            attrValueDict[key][newInterval] = intervalValues

                        rules[key] = [newInterval]
                    # Endif
                # Endfor

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
                        # Endif
                    # Endfor

                    if len(testBlock) and testBlock.issubset(originalGoal):
                        rules.pop(attribute, None)
                    # Endif
                # Endfor

                # Add the new rule (with dropped values) to the ruleset
                ruleSet.append([rules, [attrDecision,  decision]])
                rules = dict()
                numericRuleVals = dict()
                runningBlock = set()
            else:
                goal = matchedGoal
        # Endwhile
    # Endfor

    # Convert the induced rules to a friendly format
    finalRules = makeFriendlyRules(ruleSet)

    #if DEBUG:
    ruleStr = "Certain" if __calcCertain__ else "Possible"
    print("{} rules have been induced:".format(ruleStr))
    if not finalRules:
        print("  **No rules were produced of this type.\n")
    else:
        listPrint(finalRules)

    printOutput(finalRules)

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
        # Endfor
        friendlyRule += " -> ({}, {})".format(rule[1][0], rule[1][1])

        friends.append(friendlyRule)
    # Endfor

    return friends

# Calculates the set of rules based off of user input
# Choice 1: Calculates the set of certain rules
# Choice 2: Calculates the set of possible rules
# Asks the user if they want to optionally calculate the other set of rules (certain vs possible)
def calculateRules(universe, attributes, attrValueDict, attrTypes, concepts):
    # Generate the corresponding sets (A* if complete, characteristic sets if not complete)
    if not __incompleteDataset__:
        sets = calculateAStar(universe)
    else:
        sets = calculateCSets(universe, attrValueDict, attributes, attrTypes, concepts)

    # Ask the user what __calcCertain__ they want to generate.
    global __calcCertain__
    __calcCertain__ = getRuleType()

    # Generate lower approximations by default (used by certain and checked against by possible)
    global lowerApproximations
    lowerApproximations = calculateApprox(sets, concepts, "lower")

    if __calcCertain__:
        goals = lowerApproximations
    else:
        goals = calculateApprox(sets, concepts, "upper")

    mlem2(attrValueDict, attrTypes, goals, attributes[-1])

    # Ask the user if they want to calculate the other set of rules (certain or possible)
    # Might as well ask while the memory is hot and all the preprocessing has been done
    if calculateOtherSet():
        # Use the other approximations
        if __calcCertain__:
            goals = calculateApprox(sets, concepts, "upper")
            __calcCertain__ = False
        else:
            goals = lowerApproximations
            __calcCertain__ = True

        mlem2(attrValueDict, attrTypes, goals, attributes[-1])
    # Endif

# Prints the output ruleSet to a filename given by the user
def printOutput(ruleSet):
    print("-------------------------------------------------------------\n")
    outputFileName = input("What is the name of the output file?\t\t")
    print("\nFile accepted: [{}]; exporting rules...\n".format(outputFileName))
    outputFile = open(outputFileName, "w")

    for rule in ruleSet:
        outputFile.write("%s\n" % rule)

    print("Rules exported successfully.\n".format(outputFileName))

# The main function of the MLEM2 algorithm program
# Accepts an __inputFile__ from the user to parse.
# Prompts user for a type of ruleset to compute (certain rules vs. possible rules)
# Finally, computes the rulesets using the MLEM2 algorithm.
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

    ###############################################################################################
    #
    #   Preprocessing
    #
    ###############################################################################################
    # Store the concepts of this dataset
    concepts = calculateConcepts(universe)

    #Determine what types the attributes are
    attrTypes = attributeTypes(universe, attributes)
    attrValueDict = collections.OrderedDict()

    # Generate the attribute value pairs and their blocks
    for index, attrType in enumerate(attrTypes):
        attribute = attributes[index]
        attrValueDict[attribute] = generateAVBlocks(universe, index, attrType, attribute, concepts)
    # Endfor

    if DEBUG:
        for attribute, values in attrValueDict.items():
            for value, cases in values.items():
                print("({}, {}){}".format(attribute, value, cases))

        sys.exit()

    ###############################################################################################
    #
    #   Rule Induction
    #
    ###############################################################################################
    # Calculate the rulesets from the universe/attributes
    calculateRules(universe, attributes, attrValueDict, attrTypes, concepts)

main()
