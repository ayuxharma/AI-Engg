import time

# making a decorator function that will measure the execution time of any function it decorates
def timer(func):
    
    def wrapper (*args, **kwargs) :
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"Execution time for {func.__name__}: {end_time - start_time} seconds")
        return result
    return wrapper


# like a toll plaza, wahan se hokr he idhar aayega
@timer
def example_function(n) :
    time.sleep(n)
    
example_function(2)
print("Hello, World!")
