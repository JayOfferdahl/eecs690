import re, sys
import time


def listPrint(list):
    for token in list:
        print(token)

# Parses the input file and stores all relevant information for parsing.
# Modifies the array of cases to include the universe of cases
#   Each case has a list of indicies to a dictionary key which specifies the value of the attribute
# Modifies the dictionary of attributes to include all attributes values seen
def parseFile(file, attributes):
    print("Parsing input file", end = "", flush = True)
    for i in range(0, 3):
        print(".", end = "", flush = True)
        time.sleep(.5)
    print("\n")

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

    listPrint(universe)
    print()
    # return the dictionary

# The main function of the MLEM2 algorithm program
# Accepts an inputFile from the user to parse. Checks if the file can be opened, if so, prompts the
# user for a calculation method (certain vs possible rulesets). Finally, computes the rulesets
# using the MLEM2 algorithm.
#
# Handles numerical attribute values using the all cutoffs approach
# Handles missing attribute values using concept approximations
def main():
    print("-------------------------------------") 
    print("|  Welcome to Jay's MLEM2 Program!  |")
    print("|  EECS690 - Data Mining Fall 2016  |")
    print("-------------------------------------") 
    inputFile = input("\nWhat is the name of the data file you want to evaluate?\t")

    while True:
        try:
            file = open(inputFile)
            break
        except IOError:
            inputFile = input("Error, the file could not be opened. Try again:\t\t")

    print("\nInput file accepted: [{}]\n".format(inputFile))

    # Parse the input file to generate the universe of cases
    attributes = []
    universe = parseFile(file, attributes)

    print("What do you want to calculate?\n\t1. Certain Rules\n\t2. Possible Rules\n")

    while True:
        try:
            choice = int(input("Choice: "))

            if choice >= 1 and choice <= 2:
                break
        except ValueError:
            print("Please enter a number.")

    print("\nChoice {} accepted.\n".format(choice))

    outputFile = input("What is the name of the output file?\t\t")

    print("\nOutput file accepted: [{}]\n".format(outputFile))

    if choice == 1:
        print("Calculating all certain rules from input dataset: [{}]\n".format(inputFile))
    else:
        print("Calculating all possible rules from input dataset: [{}]\n".format(inputFile))

main()
