// 슬라이드 p13-v12-pc-attr — field: 대상은 무시된다, C# 12.0
#if FIELD
class P2([field: Tag("field")] int x) { public int X => x; }
#endif
