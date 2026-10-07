// 슬라이드 p15-v14-xm-indexer — C# 14 에 없는 것: 확장 인덱서, C# 14
using System;

static class Ext
{
    extension(string s)
    {
        public char At(int i) => s[s.Length - i];   // a method instead
#if INDEXER
        public char this[Index i] => s[i];          // C# 15 (preview)
#elif EVENT
        public event Action Changed { add { } remove { } }
#elif CTOR
        public extension(int n) { }
#endif
    }
}

class Program
{
    static void Main() => Console.WriteLine("abc".At(1));
}
