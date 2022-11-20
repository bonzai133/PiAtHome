from pyownet import protocol


def main():
    owproxy = protocol.proxy(host="192.168.0.99", port=4304)
    print(owproxy.dir())
    print(owproxy.read('28.3CDDCD040000/temperature'))
    print(owproxy.read('26.31AD88010000/temperature'))


if __name__ == "__main__":
    main()
