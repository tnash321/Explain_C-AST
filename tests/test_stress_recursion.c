#include <stdio.h>

int recursive_sum(int n) {
    if (n <= 0) {
        return 0;
    }

    return n + recursive_sum(n - 1);
}

void stress_recursion_loop(int n) {
    int total = 0;

    for (int i = 0; i < n; i++) {
        total += recursive_sum(i);
    }

    printf("total = %d\n", total);
}

int main() {
    stress_recursion_loop(10);
    return 0;
}