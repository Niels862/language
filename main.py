from executor import execute


def main():
    with open("script", "r") as file:
        execute(file.read())


if __name__ == '__main__':
    main()
