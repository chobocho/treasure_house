// 슬라이드 p4-v19-aliasrepair — 옛 자리에 남긴 전달용 별칭
package oldpkg

import "ex/04/aliasrepair/newpkg"

// Config is kept so that old clients still compile.
//
// Deprecated: use newpkg.Config.
type Config = newpkg.Config
