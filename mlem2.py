import re
import sys
import time

inputFileName = ""
outputFileName = ""
DEBUG = 1

# Prints out a list token by token, separating tokens with a newline
def listPrint(list):
    for token in list:
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

# Calculates the set of rules based off of user input
# Choice 1: Calculates the set of certain rules
# Choice 2: Calculates the set of possible rules
# Returns the set of rules that were calculated given the user input choice
def calculateRules(universe, attributes):
    choice = getRuleType()

    # Determine what types the attributes are
    attrTypes = attributeTypes(universe, attributes)
    rules = attributes

    return rules

# Prints the output ruleSet to a filename given by the user
def printOutput(ruleSet):
    outputFileName = input("What is the name of the output file?\t\t")
    print("\nOutput file accepted: [{}]\n".format(outputFileName)) 
    outputFileName = open(outputFileName, "w")

    for rule in ruleSet:
        outputFileName.write("%s\n" % rule)

    # DEBUG print the ruleset generated at the very end
    if DEBUG:
        listPrint(ruleSet)

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

    # Calculate the rulesets from the universe/attributes
    ruleSet = calculateRules(universe, attributes)

    # Print the output to the desired file
    printOutput(ruleSet)

main()
