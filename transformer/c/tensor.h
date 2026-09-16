/* tensor.h — float32 평면 버퍼의 기본 연산. 행 우선(SPEC §2). */
#ifndef TFS_TENSOR_H
#define TFS_TENSOR_H

void tfs_matmul_ijk(float *out, const float *a, const float *b, int n,
                    int m, int p);
void tfs_matmul_ikj(float *out, const float *a, const float *b, int n,
                    int m, int p);
void tfs_matmul_blocked(float *out, const float *a, const float *b,
                        int n, int m, int p, int block);
void tfs_transpose(float *out, const float *a, int n, int m);
void tfs_add_bias(float *x, const float *b, int rows, int cols);

#endif
