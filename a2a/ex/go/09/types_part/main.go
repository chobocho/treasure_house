// Part 의 네 내용 — 생성 함수, 읽는 메서드, 타입 스위치.
//
//	go run ./09/types_part
package main

import (
	"fmt"

	"github.com/a2aproject/a2a-go/v2/a2a"
)

func main() {
	// region: make
	parts := []*a2a.Part{
		a2a.NewTextPart("30명"),
		a2a.NewDataPart(map[string]any{"headcount": 30}),
		a2a.NewRawPart([]byte("안녕")),
		a2a.NewFileURLPart("https://x.example/menu.pdf",
			"application/pdf"),
		a2a.NewTextPart(""), // 빈 글
	}
	// endregion
	// region: read
	for _, p := range parts {
		// 메서드 넷은 다른 종류면 영값을 준다 — 오류가 아니다
		fmt.Printf("Text()=%q Data()=%v Raw()=%v URL()=%q\n",
			p.Text(), p.Data(), p.Raw(), p.URL())
		switch c := p.Content.(type) { // 종류는 타입 스위치로
		case a2a.Text:
			fmt.Println("  → 글", len(c), "바이트")
		case a2a.Data:
			fmt.Printf("  → 데이터 %T\n", c.Value)
		case a2a.Raw:
			fmt.Println("  → 바이트", len(c), "개")
		case a2a.URL:
			fmt.Println("  → 주소", p.MediaType)
		}
	}
	// endregion
}
