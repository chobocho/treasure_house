// 슬라이드 p5-v116-metrics — 이름으로 읽는 런타임 지표, Go 1.16
package main

import (
	"fmt"
	"runtime/metrics"
	"strings"
)

func main() {
	var samples []metrics.Sample
	for _, d := range metrics.All() {
		if strings.HasPrefix(d.Name, "/gc/heap/") {
			samples = append(samples, metrics.Sample{Name: d.Name})
		}
	}
	metrics.Read(samples)
	for _, s := range samples {
		kind := map[metrics.ValueKind]string{
			metrics.KindUint64:           "uint64",
			metrics.KindFloat64:          "float64",
			metrics.KindFloat64Histogram: "histogram",
		}[s.Value.Kind()]
		fmt.Printf("%-32s %s\n", s.Name, kind)
	}
}
