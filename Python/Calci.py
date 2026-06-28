def add (n1, n2):
    return n1 + n2

def subtract (n1, n2):
    return n1 - n2      

def multiply (n1, n2):
    return n1 * n2  

def divide (n1, n2):
    if n2 == 0:
        raise ValueError("Cannot divide by zero.")
    return n1 / n2

print("Select operation:")
print("1. Add")
print("2. Subtract")
print("3. Multiply")
print("4. Divide")

select = input("Enter choice (1/2/3/4): ")

if select in ('1', '2', '3', '4'):
    num1 = float(input("Enter first number: "))
    num2 = float(input("Enter second number: "))

    if select == '1':
        print(num1, "+", num2, "=", add(num1, num2))

    elif select == '2':
        print(num1, "-", num2, "=", subtract(num1, num2))

    elif select == '3':
        print(num1, "*", num2, "=", multiply(num1, num2))

    elif select == '4':
        try:
            result = divide(num1, num2)
            print(num1, "/", num2, "=", result)
        except ValueError as e:
            print(e)
else:
    print("Invalid input")
