import re, sys





# The main function of the MLEM2 algorithm program
# Accepts a filename from the user to parse. Checks if the file can be opened, if so, prompts the
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
    textInput = input("\nWhat is the name of the data file you want to evaluate?\t")

    while True:
        try:
            file = open(textInput)
            break
        except IOError:
            textInput = input("Error, the file could not be opened. Try again:\t\t")

    print("\nInput file accepted.\n")
    print("What do you want to calculate?\n\t1. Certain Rules\n\t2. Possible Rules\n")

    while True:
        try:
            choice = int(input("Choice: "))

            if choice >= 1 and choice <= 2:
                break
        except ValueError:
            print("Please enter a number.")

    print("\nChoice accepted.\n")

    if choice == 1:
        print("Calculating all certain rules from input dataset [{}]\n".format(textInput))
    else:
        print("Calculating all possible rules from input dataset [{}]\n".format(textInput))

main()
