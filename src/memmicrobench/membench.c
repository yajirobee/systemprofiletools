#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <sched.h>
#include <numa.h>
#include <time.h>
#include <sys/types.h>
#include <unistd.h>
#include <assert.h>
#include "util.h"

typedef struct {
    unsigned long ops;
    unsigned long clk;
    double wallclocktime;
} perf_counter_t;

typedef struct {
  perf_counter_t pc;
  int destnode;
  long *working_area;
  long working_size;
} mem_bench_info_t;

struct {
  int usecore;
  long access_size;
  double timeout;
} option;

void
parsearg(int argc, char **argv)
{
  int opt;

  option.usecore = 1;
  option.access_size = 1 << 20;
  option.timeout = 10 * 1000 * 1000.0; // default timeout is 10 seconds

  while ((opt = getopt(argc, argv, "c:s:t:")) != -1) {
    switch (opt) {
    case 'c':
      option.usecore = atoi(optarg);
      break;
    case 's':
      option.access_size = procsuffix(optarg);
      break;
    case 't':
      option.timeout = atof(optarg) * 1000000.0;
      break;
    default:
      fprintf(stderr, "Usage : %s [-c cpuno] [-s accesssize] [-t timeout(sec)]\n", argv[0]);
      exit(EXIT_FAILURE);
    }
  }
}

static inline uint64_t
read_tsc(void)
{
    uintptr_t ret;
    uint32_t eax, edx;
    __asm__ __volatile__("cpuid; rdtsc;"
                         : "=a" (eax) , "=d" (edx)
                         :
                         : "%ebx", "%ecx");
    ret = ((uint64_t)edx) << 32 | eax;
    return ret;
}

static inline void
swap_long(long *ptr1, long *ptr2)
{
    long tmp;
    if (ptr1 != ptr2) {
        tmp = *ptr1;
        *ptr1 = *ptr2;
        *ptr2 = tmp;
    }
}

void
memory_stress_rand(perf_counter_t *pc,
                   long *working_area,
                   long working_size)
{
  register unsigned long i;
  register long *ptr;
  long *ptr_start;
  unsigned long *shufflearray;
  const unsigned long niter = 2 << 10;
  struct timespec stime, ftime;

  register uintptr_t t0, t1;

  {
    // initialize shuffled pointer loop
    const unsigned long ncacheline = working_size / CACHELINE_SIZE;
    const unsigned long step = CACHELINE_SIZE / sizeof(long);
    unsigned long offset, tmp;
    if ((shufflearray = (unsigned long *)calloc(ncacheline, sizeof(long))) == NULL) {
      perror("calloc()");
      exit(EXIT_FAILURE);
    }
    for (i = 0; i < ncacheline; i++){ shufflearray[i] = i; }
    for (i = 0; i < ncacheline; i++){
      offset = drand48() * ncacheline;
      tmp = shufflearray[i];
      shufflearray[i] = shufflearray[offset];
      shufflearray[offset] = tmp;
    }
    ptr_start = working_area + (shufflearray[0] * step);
    for (i = 1, ptr = ptr_start; i < ncacheline; i++, ptr = (long *)*ptr){
      *ptr = (long)(working_area + (shufflearray[i] * step));
    }
    *ptr = (long)ptr_start;
    free(shufflearray);

    // check loop
    for (i = 1, ptr = (long *)*ptr_start; i < ncacheline; i++, ptr = (long *)*ptr) { }
    if (ptr != ptr_start) {
      fprintf(stderr, "initialization failed : broken loop\n");
      exit(EXIT_FAILURE);
    }
  }

  CLOCK_GETTIME(&stime);
  CLOCK_GETTIME(&ftime);
  while (TIMEINTERVAL_SEC(stime, ftime) < option.timeout) {
    t0 = read_tsc();
    ptr = ptr_start;
    for (i = 0; i < niter; i++){
#include "membench-inner-rand.c"
    }
    t1 = read_tsc();
    pc->clk += t1 - t0;
    pc->ops += niter * MEM_INNER_LOOP_RANDOM_NUM_OPS;
    CLOCK_GETTIME(&ftime);
  }
  pc->wallclocktime = TIMEINTERVAL_SEC(stime, ftime);
}

void
numa_membench(mem_bench_info_t *mbinfo)
{

  assert(mbinfo->destnode <= numa_max_node());

  {
    long size, freep;
    size = numa_node_size(mbinfo->destnode, &freep);
    //printf("node %d : total = %ld(B), free = %ld(B)\n", mbinfo->destnode, size, freep);
    assert(freep >= mbinfo->working_size);

    mbinfo->working_area =
      (long *)numa_alloc_onnode(mbinfo->working_size, mbinfo->destnode);
    if (NULL == mbinfo->working_area) {
      perror("numa_alloc_onnode");
      exit(EXIT_FAILURE);
    }
    memset(mbinfo->working_area, 0, mbinfo->working_size);
  }

  memory_stress_rand(&mbinfo->pc, mbinfo->working_area, mbinfo->working_size);

  // release resources
  numa_free(mbinfo->working_area, mbinfo->working_size);
}

int
main(int argc, char **argv)
{
  int i;
  cpu_set_t cpuset;
  mem_bench_info_t mbinfo;

  if (numa_available() == -1){
    fprintf(stderr, "numa functions aren't available\n");
    exit(EXIT_FAILURE);
  }

  parsearg(argc, argv);
  mbinfo.working_size = option.access_size;

  // set affinity
  CPU_ZERO(&cpuset);
  CPU_SET(option.usecore, &cpuset);
  sched_setaffinity(getpid(), sizeof(cpu_set_t), &cpuset);

  // read benchmark
  printf("===========================================\n"
         "memory benchmark\n"
         "===========================================\n");
  for (i = 0; i <= numa_max_node(); i++) {
    mbinfo.destnode = i;
    mbinfo.pc.ops = 0;
    mbinfo.pc.clk = 0;
    numa_membench(&mbinfo);
    printf("node %d :\n"
           "access_size\t%ld\n"
           "total_ops\t%ld\n"
           "total_clk\t%ld\n"
           "elapsed_time\t%.9f\n"
           "ops_per_sec\t%le\n"
           "clk_per_op\t%le\n"
           "(usec_per_op\t%lf)\n",
           i,
           mbinfo.working_size,
           mbinfo.pc.ops,
           mbinfo.pc.clk,
           mbinfo.pc.wallclocktime,
           mbinfo.pc.ops / mbinfo.pc.wallclocktime,
           ((double)mbinfo.pc.clk) / mbinfo.pc.ops,
           mbinfo.pc.wallclocktime * 1000000 / mbinfo.pc.ops
           );
  }

  return 0;
}
