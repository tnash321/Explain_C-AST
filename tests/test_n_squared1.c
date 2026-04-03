// test_for_n2.c
#include <stdio.h>

int main() {
    int n = 10;
    int count = 0;

    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            printf("i = %d, j = %d\n", i, j);
            count++;
        }
    }

    printf("Total iterations = %d\n", count);
    return 0;
}