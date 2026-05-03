#include <mpi.h>
#include <stdio.h>

int main(int argc, char **argv) {
    int rank;
    int size;
    int local_value;
    int total_value;

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    for (int i = 0; i < 10; i++) {
        local_value = rank + i;

        MPI_Reduce(
            &local_value,
            &total_value,
            1,
            MPI_INT,
            MPI_SUM,
            0,
            MPI_COMM_WORLD
        );

        printf("rank %d iteration %d total %d\n", rank, i, total_value);
    }

    MPI_Finalize();
    return 0;
}