/* ops.h — 부품 커널. 역전파는 전부 += 로 쌓는다(파이썬과 같은 규칙). */
#ifndef TFS_OPS_H
#define TFS_OPS_H

#define TFS_LN_EPS 1e-5
#define TFS_GELU_A 0.7978845608028654
#define TFS_GELU_B 0.044715

void tfs_softmax_row(float *p, const float *z, int n);
void tfs_softmax_row_backward(float *dz, const float *p,
                              const float *dp, int n);
double tfs_cross_entropy_row(float *p, const float *z, int n,
                             int target);
void tfs_cross_entropy_backward_row(float *dz, const float *p, int n,
                                    int target, float scale);
void tfs_layernorm_forward(float *y, float *xhat, float *sinv,
                           const float *x, const float *g,
                           const float *b, int rows, int n);
void tfs_layernorm_backward(float *dx, float *dg, float *db,
                            const float *dy, const float *xhat,
                            const float *sinv, const float *g, int rows,
                            int n);
void tfs_gelu_forward(float *y, const float *x, int n);
void tfs_gelu_backward(float *dx, const float *x, const float *dy,
                       int n);

#endif
