// 슬라이드 p15-v14-xm-state — 확장 블록에는 상태를 둘 곳이 없다, C# 14
using System;

static class Ext
{
    extension(string s)
    {
        public int Twice => s.Length * 2;      // computed: fine
#if AUTO
        public int Hits { get; set; }          // auto-property
#elif FIELD
        int hits;                              // a field
#elif KW
        public int Len { get => field; }       // the field keyword
#elif INIT
        public int Size { init { } }           // init accessor
#endif
    }
}

class Program
{
    static void Main() => Console.WriteLine("abc".Twice);
}
