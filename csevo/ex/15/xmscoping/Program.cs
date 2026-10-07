// 슬라이드 p15-v14-xm-scoping — 블록의 이름이 보이는 범위, C# 14
using System;
using System.Linq;

static class E
{
    extension<T>(T[] ts)
    {
        public bool Has(T t) => ts.Contains(t);  // T and ts in scope
        public static string Name() => nameof(ts); // nameof is allowed
#if STATIC
        public static int Count() => ts.Length;  // ts from static
#elif REUSE
        public void Put(int ts) { }              // reuses 'ts'
#elif TPARAM
        public void Map<T>() { }                 // reuses 'T'
#endif
    }
}

class Program
{
    static void Main()
    {
        int[] xs = { 1, 2, 3 };
        Console.WriteLine(xs.Has(2) + " " + E.Name<int>());
    }
}
