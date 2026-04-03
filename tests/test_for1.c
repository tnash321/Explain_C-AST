// test_for_linear.c
#include <stdio.h>

int main() {
    int n = 10;
    int sum = 0;

    for (int i = 0; i < n; i++) {
        printf("i = %d\n", i);
        sum += i;
    }

    printf("Sum = %d\n", sum);
    return 0;
}