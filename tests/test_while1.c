#include <stdio.h>

void log_message(int x) {
    printf("Logging value: %d\n", x);
}

int compute(int a) {
    return a * 2;
}

void send_data(int value) {
    printf("Sending data: %d\n", value);
}

int main() {
    int i = 0;
    int limit = 5;

    while (i < limit) {
        int result = compute(i);

        log_message(result);

        if (result % 2 == 0) {
            send_data(result);
        }

        i++;
    }

    return 0;
}
