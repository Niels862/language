from executor import execute
from time import perf_counter_ns


def main():
    start = perf_counter_ns()
    with open("script", "r") as file:
        execute(file.read())
    print(f"Finished in {(perf_counter_ns() - start) / 1e9}s")


if __name__ == '__main__':
    main()
