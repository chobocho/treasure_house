// 슬라이드 p5-v115-small — SubexpIndex·Redacted·FormatComplex, Go 1.15
package main

import (
	"fmt"
	"net/url"
	"regexp"
	"strconv"
)

func main() {
	re := regexp.MustCompile(`(?P<year>\d{4})-(?P<month>\d{2})`)
	m := re.FindStringSubmatch("released 2020-08")
	fmt.Println("month:", m[re.SubexpIndex("month")])

	u, _ := url.Parse("https://alice:s3cret@example.com/db")
	fmt.Println(u.Redacted())

	c := complex(1.5, -2)
	s := strconv.FormatComplex(c, 'f', 1, 128)
	back, err := strconv.ParseComplex(s, 128)
	fmt.Println(s, back == c, err)
}
