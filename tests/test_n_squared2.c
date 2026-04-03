// test_for_nested_variable.c
#include <stdio.h>

int main() {
    int n = 10;

    for (int i = 0; i < n; i++) {
        for (int j = 0; j < i; j++) {
            printf("%d %d\n", i, j);
        }
    }

    return 0;
}