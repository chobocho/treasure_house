// excerpt of $GOROOT/src/internal/godebugs/table.go (go1.27.1)
var All = []Info{
	{Name: "allowmultiplevcs", Package: "cmd/go"},
	{Name: "httplaxcontentlength", Package: "net/http", Changed: 22, Old: "1"},
	{Name: "httpmuxgo121", Package: "net/http", Changed: 22, Old: "1"},
	{Name: "jstmpllitinterp", Package: "html/template", Opaque: true}, // bug #66217: remove Opaque
	//{Name: "multipartfiles", Package: "mime/multipart"},
	{Name: "panicnil", Package: "runtime", Changed: 21, Old: "1"},
	{Name: "tlsmaxrsasize", Package: "crypto/tls"},
}
