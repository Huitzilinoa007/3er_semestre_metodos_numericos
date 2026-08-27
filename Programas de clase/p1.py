def main():
    print("Ingrese un número: ")
    num = int(input())
    print(int_to_bin(num))

def int_to_bin(deci, bits):
    bin = []

    while(deci > 0):
        num = deci
        deci = deci//2
        residuo = num - (deci*2)
        bin.append(residuo)

    return bin

main()