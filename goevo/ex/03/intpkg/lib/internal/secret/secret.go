// 슬라이드 p3-v14-internal — lib 안에서만 쓰는 패키지, Go 1.4
package secret

// Key is exported, yet only lib/... may import this package.
const Key = "s3cr3t"
