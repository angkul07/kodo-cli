def add(x, y):
    return x + y

def subtract(x, y):
    return x - y

def multiply(x, y):
    return x * y

def divide(x, y):
    if y == 0:
        raise ValueError("Cannot divide by zero!")
    return x / y

def run_calculator():
    """Runs a simple command-line calculator."""
    print("\n--- Simple Python Calculator ---")
    print("Enter 'quit' to exit.")
    print("Format: number operator number (e.g., 2 + 3)")

    while True:
        try:
            expression = input("\n> ")
            if expression.lower() == 'quit':
                break

            parts = expression.split()
            if len(parts) != 3:
                print("Invalid expression format. Please use 'number operator number' (e.g., 2 + 3).")
                continue

            num1 = float(parts[0])
            operator = parts[1]
            num2 = float(parts[2])

            result = None
            if operator == '+':
                result = add(num1, num2)
            elif operator == '-':
                result = subtract(num1, num2)
            elif operator == '*':
                result = multiply(num1, num2)
            elif operator == '/':
                result = divide(num1, num2)
            else:
                print("Invalid operator. Please use +, -, *, or /.")
                continue

            print(f"Result: {result}")

        except ValueError as ve:
            print(f"Error: {ve}")
        except ZeroDivisionError:
            print("Error: Division by zero is not allowed.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    print("Calculator session ended. Goodbye!")

if __name__ == "__main__":
    run_calculator()
