/* pool.c — 정적 분할 스레드 묶음.
 *
 * 연산 하나마다 스레드를 새로 만들면(pthread_create) 한 스텝에 수백 번
 * 만들어 부수느라 계산보다 준비가 길어진다. 스레드는 한 번만 띄워
 * 두고, 일감이 오면 깨워 조각 하나씩 맡긴다.
 *
 * 결정론의 뿌리는 두 가지다(SPEC §8).
 *   1. 조각 경계는 n 과 스레드 수로만 정해진다: t 번 조각은
 *      [n·t/P, n·(t+1)/P).
 *   2. 커널은 출력 칸 하나를 한 조각에서만, 정해진 차례로 계산한다.
 *      그래서 스레드 수가 달라도 칸마다 더하는 차례가 같고, 결과는
 *      비트까지 같다.
 * 조각 0 은 부른 스레드가 직접 한다.
 */
#define _POSIX_C_SOURCE 200809L
#include <pthread.h>
#include <stdlib.h>

#include "pool.h"

static struct {
    int threads, alive;
    pthread_t *tid;
    pthread_mutex_t mu;
    pthread_cond_t go, done;
    long job;                 /* 일감 번호 — 늘어나면 새 일감이다 */
    int remaining;            /* 아직 안 끝난 일꾼 조각 수 */
    int n;
    tfs_range_fn fn;
    void *ctx;
} P = {1, 0, NULL, PTHREAD_MUTEX_INITIALIZER, PTHREAD_COND_INITIALIZER,
       PTHREAD_COND_INITIALIZER, 0, 0, 0, NULL, NULL};

static void chunk(int t, int n, int *lo, int *hi)
{
    *lo = (int)((long)n * t / P.threads);
    *hi = (int)((long)n * (t + 1) / P.threads);
}

static void *worker(void *arg)
{
    int t = (int)(long)arg;
    long seen = 0;

    pthread_mutex_lock(&P.mu);
    for (;;) {
        while (P.alive && P.job == seen)
            pthread_cond_wait(&P.go, &P.mu);
        if (!P.alive)
            break;
        seen = P.job;
        {
            int lo, hi;
            tfs_range_fn fn = P.fn;
            void *ctx = P.ctx;
            chunk(t, P.n, &lo, &hi);
            pthread_mutex_unlock(&P.mu);
            if (lo < hi)
                fn(ctx, lo, hi);
            pthread_mutex_lock(&P.mu);
        }
        if (--P.remaining == 0)
            pthread_cond_signal(&P.done);
    }
    pthread_mutex_unlock(&P.mu);
    return NULL;
}

void tfs_pool_init(int threads)
{
    int t;

    P.threads = threads < 1 ? 1 : threads;
    P.alive = 1;
    P.job = 0;
    P.tid = malloc(sizeof(pthread_t) * (size_t)P.threads);
    for (t = 1; t < P.threads; t++)
        pthread_create(&P.tid[t], NULL, worker, (void *)(long)t);
}

void tfs_pool_free(void)
{
    int t;

    pthread_mutex_lock(&P.mu);
    P.alive = 0;
    pthread_cond_broadcast(&P.go);
    pthread_mutex_unlock(&P.mu);
    for (t = 1; t < P.threads; t++)
        pthread_join(P.tid[t], NULL);
    free(P.tid);
    P.tid = NULL;
    P.threads = 1;
}

int tfs_pool_threads(void)
{
    return P.threads;
}

void tfs_parallel_for(int n, tfs_range_fn fn, void *ctx)
{
    int lo, hi;

    if (P.threads == 1 || n < 2) {
        fn(ctx, 0, n);
        return;
    }
    pthread_mutex_lock(&P.mu);
    P.fn = fn;
    P.ctx = ctx;
    P.n = n;
    P.remaining = P.threads - 1;
    P.job++;
    pthread_cond_broadcast(&P.go);
    pthread_mutex_unlock(&P.mu);

    chunk(0, n, &lo, &hi);
    if (lo < hi)
        fn(ctx, lo, hi);

    pthread_mutex_lock(&P.mu);
    while (P.remaining > 0)
        pthread_cond_wait(&P.done, &P.mu);
    pthread_mutex_unlock(&P.mu);
}
