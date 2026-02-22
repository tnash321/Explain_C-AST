#include <stdio.h>

int main() {
    int matrix[5][5];
    int sum = 0;

    // Outer loop
    for (int i = 0; i < 5; i++) {

        // Inner loop
        for (int j = 0; j < 5; j++) {
            matrix[i][j] = i * j;     // independent computation
            sum += matrix[i][j];      // reduction-style pattern
            printf("Value: %d\n", matrix[i][j]);  // I/O penalty
        }
    }

    printf("Total sum: %d\n", sum);
    return 0;
}