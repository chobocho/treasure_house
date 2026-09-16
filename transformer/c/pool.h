/* pool.h — 정적 분할 스레드 묶음 (SPEC §8).
 *
 * tfs_parallel_for(n, fn, ctx) 는 [0, n) 을 스레드 수만큼 이어진
 * 조각으로 나눠 fn(ctx, lo, hi) 를 부른다. 조각 경계는 n 과 스레드
 * 수만으로 정해지고, 각 출력 칸은 한 조각에서만 계산된다. */
#ifndef TFS_POOL_H
#define TFS_POOL_H

typedef void (*tfs_range_fn)(void *ctx, int lo, int hi);

void tfs_pool_init(int threads);
void tfs_pool_free(void);
int tfs_pool_threads(void);
void tfs_parallel_for(int n, tfs_range_fn fn, void *ctx);

#endif
