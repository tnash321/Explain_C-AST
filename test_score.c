#include <stdio.h>

void helper(int x) {
    printf("Helper called with %d\n", x);
}

int main() {
    int i = 0;

    // While loop with printf (I/O penalty test)
    while (i < 5) {
        printf("While loop iteration: %d\n", i);
        helper(i);
        i++;
    }

    printf("\nSwitching to for loop\n\n");

    // For loop with printf
    for (int j = 0; j < 5; j++) {
        printf("For loop iteration: %d\n", j);
        helper(j);
    }

    return 0;
}
