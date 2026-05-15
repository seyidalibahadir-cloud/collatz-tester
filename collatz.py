def collatz(n):
    steps = 0

    while n != 1:
        if n % 2 == 0:
            n = n // 2
        else:
            n = 3 * n + 1

        steps += 1

    return steps


LIMIT = 10000

max_steps = 0
worst_number = 1

for i in range(1, LIMIT + 1):
    s = collatz(i)

    if s > max_steps:
        max_steps = s
        worst_number = i

print("Test tamamlandı")
print("En uzun zincir:", max_steps)
print("Rekor sayı:", worst_number)
