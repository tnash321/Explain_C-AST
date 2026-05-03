#include <stdio.h>

void stress_nested_dependencies(int n, int *a, int *b) {
    int total = 0;

    for (int i = 1; i < n; i++) {
        for (int j = 1; j < n; j++) {
            a[j] = a[j - 1] + b[i];
            total += a[j];
        }
    }

    printf("total = %d\n", total);
}

int main() {
    int a[100];
    int b[100];

    for (int i = 0; i < 100; i++) {
        a[i] = i;
        b[i] = i * 2;
    }

    stress_nested_dependencies(100, a, b);
    return 0;
}