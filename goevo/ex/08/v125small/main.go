// 슬라이드 p8-v125-small — Cloner·ReadLinkFS·GroupAttrs, Go 1.25
package main

import (
	"crypto/sha256"
	"fmt"
	"hash"
	"io/fs"
	"log/slog"
	"os"
	"testing/fstest"
)

func main() {
	// hash.Cloner: fork a running hash to try two different endings.
	h := sha256.New()
	h.Write([]byte("common prefix, "))
	c, _ := h.(hash.Cloner).Clone()
	h.Write([]byte("ending A"))
	c.Write([]byte("ending B"))
	fmt.Printf("A %x…\nB %x…\n", h.Sum(nil)[:6], c.Sum(nil)[:6])

	// io/fs.ReadLinkFS: symlinks in an fs.FS (MapFS, DirFS, Root.FS).
	fsys := fstest.MapFS{
		"v1.txt": {Data: []byte("one")},
		"latest": {Data: []byte("v1.txt"), Mode: fs.ModeSymlink},
	}
	target, err := fs.ReadLink(fsys, "latest")
	fmt.Println("latest ->", target, err)
	fi, _ := fs.Lstat(fsys, "latest")
	fmt.Println("Lstat mode:", fi.Mode())

	// slog.GroupAttrs: a group from a []slog.Attr you already have.
	attrs := []slog.Attr{
		slog.Int("id", 7), slog.String("role", "admin")}
	opts := &slog.HandlerOptions{ReplaceAttr: dropTime}
	log := slog.New(slog.NewTextHandler(os.Stdout, opts))
	log.Info("login", slog.GroupAttrs("user", attrs...))
}

func dropTime(groups []string, a slog.Attr) slog.Attr {
	if a.Key == slog.TimeKey && len(groups) == 0 {
		return slog.Attr{}
	}
	return a
}
