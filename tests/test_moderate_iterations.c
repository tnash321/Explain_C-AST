// tests/test_moderate_loop.c
// Loop runs 100 iterations. It should receive a small bonus
// for a moderate iteration count.
void test_moderate_iteration_loop(void) {
    for (int i = 0; i < 100; i++) {
        // do something trivial
        double v = (double)i / 2.0;
    }
}