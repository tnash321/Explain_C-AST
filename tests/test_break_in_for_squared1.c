#include <stdio.h>

int main() {
    printf("Starting nested loop test...\n\n");

    for (int i = 1; i <= 3; i++) {
        printf("Outer loop iteration: %d\n", i);

        for (int j = 1; j <= 5; j++) {
            printf("  Inner loop iteration: %d\n", j);

            if (j == 3) {
                printf("  Break triggered at j = %d\n", j);
                break;  // This exits ONLY the inner loop
            }
        }

        printf("Back in outer loop after inner break.\n\n");
    }

    printf("Program finished.\n");
    return 0;
}