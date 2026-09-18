import sys


def parse(line):
    key, _, value = line.partition("=")
    return key.strip(), value.strip().lower()


def main():
    for line in sys.stdin:
        print(parse(line))


if __name__ == "__main__":
    main()
