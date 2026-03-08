// tests/test_large_loop.c
// Loop runs 1,000 iterations (i = 0 … 999). This should be rewarded
// as a large iteration count by your analyzer.
void test_large_iteration_loop(void) {
    for (int i = 0; i < 1000; i++) {
        // simple work
        int x = i * 2;
    }
}