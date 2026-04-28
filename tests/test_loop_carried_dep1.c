// test_loop_carried_dep1.c
#include <stdio.h>

int main(void) {
    int sum = 0;

    // Loop-carried TRUE dependency:
    // sum(i) depends on sum(i-1)
    for (int i = 1; i <= 10; i++) {
        sum = sum + i;
    }

    // Expected: 55
    printf("%d\n", sum);
    return 0;
}