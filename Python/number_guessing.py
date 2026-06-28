import random

print("Hi! Welcome to Number Guessing Game! \n You have 7 chances to guess the number.")

low = int(input("Enter the lower limit of the range: "  ))
high = int(input("Enter the upper limit of the range: " ))

num = random.randint(low, high)

# total allowed chances
chances = 7 

#guess counter
guess_count = 0

while guess_count < chances:
    guess = int(input("Guess the number: "))
    guess_count += 1

    if guess < num:
        print("Your guess is too low.")
    elif guess > num:
        print("Your guess is too high.")
    else:
        print(f"Congratulations! You've guessed the number {num} in {guess_count} tries.")
        break
else:
    print(f"Sorry! You've used all your chances. The number was {num}.")
