// 슬라이드 p15-v14-xm-parse — 13.0 이 확장 블록을 읽는 세 길, C# 14
using System;

static class E
{
#if GEN
    extension<T>(T[] a) { public int Len() => a.Length; }  // generic
#elif EMPTY
    extension(int n) { }                                   // empty
#else
    extension(int n) { public int Twice() => n * 2; }      // members
#endif
}

class Program
{
    static void Main() => Console.WriteLine("compiled");
}
