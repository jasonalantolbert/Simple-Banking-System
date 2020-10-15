# Simple Banking System
# Author: Jason Tolbert (https://github.com/jasonalantolbert)
# Python Version 3.8


# BEGINNING OF PROGRAM


# import statements
import random
import re
import sympy
import sqlite3


# Opens a database connection to account_database.sqlite as db_conn - creating the database if it doesn't exist -
# and binds the variable db_cursor to the database's cursor.
db_conn = sqlite3.connect("account_database.sqlite")
db_cursor = db_conn.cursor()


class CreditCard:
    # Class for creating a new credit card.

    # Creates a table named accounts in account_database if it does not already exist.
    # id: account identifier
    # number: card number
    # pin: card PIN
    # balance: account balance, default value 0
    db_cursor.execute("CREATE TABLE IF NOT EXISTS accounts ("
                      "id INTEGER,"
                      "number TEXT,"
                      "pin TEXT,"
                      "balance INTEGER DEFAULT 0);")

    issuer = 400000  # All card numbers created by this program begin with 400000.

    def __init__(self):
        # The __init__ method handles the attributes of each individual instance of class CreditCard.

        # Defines the instance attribute account_identifier and the identifier_is_unique variable for use in
        # the succeeding while loop.
        self.account_identifier = None
        identifier_is_unique = False

        while not identifier_is_unique or not self.account_identifier:
            # This while loop generates the account identifier.
            # The account identifier must be unique, so the loop runs as long as identifier_is_unique is false
            # (or if account_identifier is falsy, which will be the case if the program has not yet tried
            # to generate an identifier for the instance of the class.

            # Generates a random six-digit integer to be the account_identifier.
            self.account_identifier = f"{random.randint(100000000, 999999999)}"
            # Checks account_database to see if the generated identifier already exists.
            db_cursor.execute("SELECT id FROM accounts WHERE id = ?", (self.account_identifier,))
            id_from_database = db_cursor.fetchone()
            # If the generated identifier doesn't exist in the database, identifier_is_unique will be set to True.
            # Otherwise, it will be left at False, causing the while loop to run again.
            if not id_from_database:
                identifier_is_unique = True

        def get_luhn_checksum(number):
            # This method uses the Luhn algorithm to determine the checksum for the card number.
            # number: the number for which a checksum is to be generated
            # digit_list: an initially empty list intended to contain each digit of the number. Using a list allows
            # the program to easily perform the necessary mathematical operations on the number.
            # control_number: the number used to generate the checksum. Initially, this is set to 0.
            digit_list = []
            control_number = 0

            for digit in number:
                # Appends each digit of the number to digit_list.
                digit_list.append(int(digit))

            for index in range(len(digit_list)):
                # This for loop runs once for every index in digit_list.

                if (index + 1) % 2 != 0:
                    # The indexes of digit_list go from 0 to 14. For this part of the Luhn algorithm, these indexes
                    # need to be treated as if they run 1 to 15, so the if condition checks the value of index + 1.
                    # If the value of index + 1 is odd, the value of the digit at the current index will be doubled.
                    digit_list[index] *= 2

                if digit_list[index] > 9:
                    # If the value of the digit at the index is greater than 9, 9 is subtracted
                    # from it.
                    digit_list[index] -= 9

            for digit in digit_list:
                # Binds the variable control_number to the sum of every digit in digit_list.
                control_number += digit

            # Algebraically determines the nearest number to 0 that can be added to control_number to result in a
            # multiple of 10, and binds the variable checksum to it.
            x = sympy.symbols("x")
            checksum = sympy.solve(sympy.poly(control_number + x, modulus=10))[0]
            if checksum < 0:
                # If the checksum is negative, 10 is added to the checksum.
                checksum += 10
            return checksum

        # Calls get_luhn_checksum(), passing a string containing a concatenation of the issuer number (400000) and the
        # account identifier as an argument to the parameter number. The instance
        # attribute checksum is bound to the value returned by get_luhn_checksum().
        self.checksum = get_luhn_checksum(f"{CreditCard.issuer}{self.account_identifier}")

        # Binds the instance attribute card_number to a concatenation of the issuer number (400000), the account
        # identifier, and the checksum.
        self.card_number = f"{CreditCard.issuer}{self.account_identifier}{self.checksum}"
        # Binds the instance attribute pin to a string containing a random four-digit integer.
        self.pin = f"{random.randint(1000, 9999)}"

        # Inserts all information about the newly-created credit card into account_database.
        db_cursor.execute("INSERT INTO accounts (id, number, pin) VALUES (?, ?, ?)",
                          (self.account_identifier, self.card_number, self.pin))
        # Commits pending database transactions.
        db_conn.commit()

    def __str__(self):
        # The __str__ method returns the number and pin of a given instance of class CreditCard in a
        # user-friendly message.
        return f"Your card number:\n" \
               f"{self.card_number}\n" \
               f"Your card PIN:\n" \
               f"{self.pin}\n"


def create_account():
    # Binds the variable new_card to a new instance of class CreditCard and prints a message notifying the user
    # that a card has been created.
    new_card = CreditCard()
    print(f"\nYour card has been created\n"
          f"{new_card.__str__()}")


def log_in(login_number, login_pin):
    # This function contains the functions of the banking system that can only be accessed while the user is logged in,
    # as well as the login authentication itself.
    # login_number: a card number, passed from main_menu()
    # login_pin: a PIN, passed from main_menu()

    # The variable first_run determines whether or not the succeeding while loop is being run for the first time.
    # Initially, it's set to true.
    first_run = True

    while True:
        # This loop runs infinitely until the user commands it to exit by either logging out or exiting the program.

        # BEGIN LOGIN OPTION FUNCTIONS
        def balance():
            # This function gets and returns the balance of the logged-in account.
            db_cursor.execute("SELECT balance FROM accounts WHERE number = ?", (login_number,))
            card_balance = "".join(re.findall('[0-9]', str(db_cursor.fetchone())))
            return f"\nBalance: {card_balance}\n"

        def add_income():
            # This function allows the user to add money to the logged-in account.
            income = input("\nEnter income:\n")
            db_cursor.execute("UPDATE accounts SET balance = balance + ? WHERE number = ?", (income, login_number))
            db_conn.commit()
            print("Income was added!\n")

        def do_transfer():
            # This function allows to user to transfer money to another account.

            # Binds the variable current_balance to the value of the balance of the logged-in account.
            current_balance = int(''.join(re.findall('[0-9]', balance())))

            def luhn_verify(number_to_verify):
                # Verifies that the card number of the account the user wishes to transfer money to passes the
                # Luhn algorithm.
                # number_to_verify: receiving account number, passed from outer function do_transfer()
                digit_list = []
                control_number = 0

                for digit in number_to_verify:
                    digit_list.append(int(digit))

                for index in range(len(digit_list)):
                    if (index + 1) % 2 != 0 and index < 15:
                        digit_list[index] *= 2
                    if digit_list[index] > 9 and index < 15:
                        digit_list[index] -= 9

                for index in range(len(digit_list)):
                    if index < 15:
                        control_number += digit_list[index]

                x = sympy.symbols("x")
                checksum = sympy.solve(sympy.poly(control_number + x, modulus=10))[0]
                if checksum < 0:
                    checksum += 10
                if digit_list[-1] == checksum:
                    return True  # Returns True if the Luhn algorithm was passed.
                else:
                    return False  # Returns False if the Luhn algorithm was not passed.

            print("\nTransfer")
            # Asks the user for the card number of the account they wish to transfer money to.
            receiving_account = input("Enter card number:\n")

            # Checks that the receiving account's number is different than that of the logged-in account.
            if receiving_account != login_number:

                # Checks that the receiving account's number passes the Luhn algorithm.
                if luhn_verify(receiving_account):
                    db_cursor.execute("SELECT number FROM accounts WHERE number = ?", (receiving_account,))

                    # Checks that the receiving account's number exists in account_database.
                    if db_cursor.fetchone():

                        # Asks the user how much money they want to transfer to the receiving account.
                        transfer_money = int(input("Enter how much money you want to transfer:\n"))

                        # Checks that the logged-in account's current balance is either greater than or equal to
                        # the amount of money the user wishes to transfer to the receiving account.
                        if current_balance >= transfer_money:

                            # Updates account_database, adding the amount of money to be transferred to the
                            # receiving account's balance and subtracting an equivalent amount of money from the
                            # logged-in account's balance.
                            db_cursor.execute("UPDATE accounts SET balance = balance + ? WHERE number = ?",
                                              (transfer_money, receiving_account))
                            db_cursor.execute("UPDATE accounts SET balance = balance - ? WHERE number = ?",
                                              (transfer_money, login_number))

                            # Commits pending database transactions.
                            db_conn.commit()

                            # Prints "Success!" to notify the user the transfer was completed.
                            print("Success!\n")
                        else:
                            # Prints "Not enough money!" if the logged-in account has less money than that which is
                            # to be transferred.
                            print("Not enough money!\n")
                    else:
                        # Prints "Such a card does not exist." if the receiving account number does not exist in
                        # account_database.
                        print("Such a card does not exist.\n")
                else:
                    # Prints "Probably you made a mistake in the card number. Please try again!" if the receiving
                    # account number does not pass the Luhn algorithm.
                    print("Probably you made a mistake in the card number. Please try again!\n")
            else:
                # Prints "You can't transfer money to the same account!" if the receiving account number is the same
                # as that of the logged-in account.
                print("You can't transfer money to the same account!\n")

        def close_account():
            # This function deletes the logged-in account from account_database.
            db_cursor.execute("DELETE FROM accounts WHERE number = ?", (login_number,))
            db_conn.commit()
            print("The account has been closed!\n")
        # END LOGIN OPTION FUNCTIONS

        # Binds the variable credentials to the entries in account_database that match login_number and login_pin.
        db_cursor.execute("SELECT number, pin FROM accounts WHERE number = ? AND pin = ?", (login_number, login_pin))
        credentials = db_cursor.fetchone()

        # Checks that credentials has a value (i.e. login_number and login_pin both exist in account_database).
        if credentials:
            if first_run:
                # If the while loop is running for the first time, the program notifies the user of a successful login,
                # then sets the variable first_run to False.
                print("\nYou have successfully logged in!\n")
                first_run = False

            # Presents the user with a list of actions they can perform. The variable login_option is
            # bound to the user's choice.
            login_option = input("1. Balance\n"
                                 "2. Add income\n"
                                 "3. Do transfer\n"
                                 "4. Close account\n"
                                 "5. Log out\n"
                                 "0. Exit\n")
        else:
            # Prints "Wrong card number or PIN!" if either login_number or login_pin do not exist in account_database
            print("\nWrong card number or PIN!\n")
            return

        # Determines which function to call based on the value of login_option.
        # Both options 4 and 5 will log the user out (i.e. return from log_in()).
        # Option 0 will close the connection to account_database exit the program.
        if login_option == "1":
            print(balance())
        elif login_option == "2":
            add_income()
        elif login_option == "3":
            do_transfer()
        elif login_option == "4":
            close_account()
            return
        elif login_option == "5":
            print("\nYou have successfully logged out!\n")
            return
        elif login_option == "0":
            print("\nBye!")
            db_conn.close()
            exit()


def main_menu():
    # This function handles the banking system's main menu.

    # Presents the user with a list of actions they can perform. The variable user_choice is
    # bound to the user's choice.
    user_choice = input("1. Create an account\n"
                        "2. Log into account\n"
                        "0. Exit\n")

    # Determines which function to call based on the value of login_option.
    # Option 0 will close the connection to account_database and exit the program.
    if user_choice == "1":
        create_account()
    elif user_choice == "2":
        card_number = input("\nEnter your card number:\n")
        pin = input("Enter your PIN:\n")
        log_in(card_number, pin)
    elif user_choice == "0":
        print("\nBye!")
        db_conn.close()
        exit()


# Calls main_menu() infinitely.
while True:
    main_menu()
