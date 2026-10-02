// 슬라이드 p8-v7_3-fixed — 패턴 기반 fixed, C# 7.3
using System;

class Pin
{
    private readonly int[] data = { 10, 20, 30 };
    // the pattern: a ref-returning GetPinnableReference
    public ref int GetPinnableReference() => ref data[0];
}

class App
{
    static unsafe void Main()
    {
        fixed (int* p = new Pin())          // any type with the pattern
        {
            Console.WriteLine(p[1]);
        }
        Span<int> s = new int[] { 1, 2, 3 };
        fixed (int* p = s)                  // Span<T> has it
        {
            Console.WriteLine(p[2]);
        }
        Span<int> empty = default;
        fixed (int* p = empty)              // nothing to pin
        {
            Console.WriteLine(p == null);
        }
        fixed (char* c = "abc")             // string: as before
        {
            Console.WriteLine(c[1]);
        }
    }
}
