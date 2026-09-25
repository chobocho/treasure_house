// 슬라이드 p8-v125-osroot — os.Root 의 새 메서드, Go 1.25
package main

import (
	"fmt"
	"os"
)

func say(what string, err error) { fmt.Printf("%-26s %v\n", what, err) }

func main() {
	dir, err := os.MkdirTemp("", "root")
	if err != nil {
		fmt.Println(err)
		return
	}
	defer os.RemoveAll(dir)
	root, err := os.OpenRoot(dir)
	if err != nil {
		fmt.Println(err)
		return
	}
	defer root.Close()

	// 1.24 had Open/Create/Mkdir/Remove/Stat; 1.25 adds these:
	say("MkdirAll conf/app", root.MkdirAll("conf/app", 0o755))
	say("WriteFile conf/app/a.toml",
		root.WriteFile("conf/app/a.toml", []byte("x=1\n"), 0o644))
	say("Symlink conf/current",
		root.Symlink("app/a.toml", "conf/current"))
	target, err := root.Readlink("conf/current")
	say("Readlink -> "+target, err)
	b, err := root.ReadFile("conf/current")
	say(fmt.Sprintf("ReadFile via link %q", b), err)

	// Still no way out of the root, whichever method is used.
	say("WriteFile ../escape", root.WriteFile("../escape", nil, 0o644))
	say("Symlink conf/pw", root.Symlink("/etc/passwd", "conf/pw"))
	_, err = root.ReadFile("conf/pw")
	say("ReadFile conf/pw", err)
	say("RemoveAll conf", root.RemoveAll("conf"))
}
