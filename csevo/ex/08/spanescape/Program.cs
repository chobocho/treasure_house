// 슬라이드 p8-v7_2-stackalloc-escape — 스택 메모리의 탈출, C# 7.2
using System;

class App
{
    static Span<int> FromHeap()
    {
        Span<int> s = new int[3];          // heap: may leave
        return s;
    }

    static Span<int> FromStack()
    {
        Span<int> s = stackalloc int[3];   // stack: must not leave
        return s;
    }

    static void Keep(ref Span<int> outer)
    {
        Span<int> s = stackalloc int[3];
        outer = s;                         // a wider place
    }

    static void Main() { }
}
