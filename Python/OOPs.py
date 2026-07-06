"""
OOPs
"""


class Car:

    # CLASS VARIABLE
    # Shared by ALL instances of the class (not tied to a single object).
    # Every time a Car (or subclass) object is created, this counter increases.
    total_cars = 0

    # CONSTRUCTOR
    # Special method called automatically when a new object is created.
    # 'self' refers to the current instance being built.
    def __init__(self, brand, model):
        # ENCAPSULATION
        # Double underscore prefix (__brand, __model) makes these "private".
        # Python does name-mangling internally (_Car__brand) to discourage
        # direct access from outside the class -> forces use of getter methods.
        self.__brand = brand
        self.__model = model

        # Increment the CLASS variable (shared across all objects),
        # accessed via the class name, not 'self'.
        Car.total_cars += 1

    # GETTER METHOD
    # Public method used to safely access the private __brand variable.
    def get_brand(self):
        return self.__brand + " is the brand of the car."

    def full_name(self):
        return f"{self.__brand} {self.__model}"

    # POLYMORPHISM
    # This method can be overridden by subclasses to provide different
    # behavior while keeping the same method name/signature.
    def fuel_type(self):
        return "The fuel type of the car is gasoline."

    # STATIC METHOD
    # Does NOT take 'self' or 'cls' — it doesn't depend on instance or class
    # data. Used for utility/helper functions logically related to the class.
    @staticmethod
    def car_description():
        return "Cars are vehicles that run on roads and are used for transportation."

    # PROPERTY (read-only)
    # Lets you access model like an attribute (car.model) instead of a
    # method call (car.model()), while still controlling access internally.
    @property
    def model(self):
        return self.__model


# INHERITANCE
# ElectricCar automatically gets all attributes/methods of Car (the parent
# class), and can add its own or override existing ones.
class ElectricCar(Car):

    def __init__(self, brand, model, battery_size):
        # super() calls the parent class's constructor to reuse its logic
        # instead of rewriting brand/model assignment again.
        super().__init__(brand, model)
        self.battery_size = battery_size

    # POLYMORPHISM (Method Overriding)
    # Same method name as in Car, but different behavior — this REPLACES
    # the parent's fuel_type() when called on an ElectricCar object.
    @staticmethod
    def fuel_type():
        return "The fuel type of the car is electricity."


# USAGE EXAMPLES

my_car = ElectricCar("Tesla", "Model S", 100)
print(my_car.get_brand())     # inherited method from Car
print(my_car.full_name())     # inherited method from Car

print(my_car.fuel_type())     # overridden version (ElectricCar's own)

alto = Car("Maruti", "Alto k10")
print(alto.fuel_type())       # original version (Car's own)

print(f"Total cars created: {Car.total_cars}")

# NOTE ON ENCAPSULATION & INHERITANCE:
# __brand is a private variable — it cannot be accessed directly from
# outside the class (e.g., my_car.__brand would fail).
# Private variables are NOT directly inherited/accessible by subclasses
# either, but subclasses CAN use public methods defined in the parent
# class (like get_brand() and full_name()) to access them indirectly.

print(Car.car_description())  # static method called on the class directly

print(f"Model of my car: {alto.model}")  # accessed like an attribute (property)

# isinstance() CHECKS
# Confirms whether an object belongs to a given class (or its parent class).
print(isinstance(my_car, Car))          # True -> ElectricCar IS-A Car (inherited)
print(isinstance(my_car, ElectricCar))  # True -> direct match


# MULTIPLE INHERITANCE
# A class can inherit from more than one parent class at the same time.
# Python looks up methods left-to-right based on the order of parent
# classes listed (this order is called the MRO - Method Resolution Order).
class Battery:
    def battery_info(self):
        return "This is a battery class."


class Engine:
    def engine_info(self):
        return "This is an engine class."


# HybridCar inherits from THREE classes: Battery, Engine, and Car.
class HybridCar(Battery, Engine, Car):
    def __init__(self, brand, model, battery_size):
        # Since Car isn't reached via a simple super() chain here (multiple
        # inheritance), we call Car's constructor explicitly by name.
        Car.__init__(self, brand, model)
        self.battery_size = battery_size


nano = HybridCar('Tata', 'Nano', 20)
print(nano.battery_info())   # method inherited from Battery
