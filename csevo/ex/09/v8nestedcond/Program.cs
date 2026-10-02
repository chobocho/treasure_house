// 슬라이드 p9-v8-nested-cond — 조건 연산자 안의 stackalloc, C# 7.2
using System;

class App
{
    static void Main()
    {
        int n = 4;                    // small: stack, large: heap
        Span<int> buf = n <= 64 ? stackalloc int[n] : new int[n];
        buf[0] = 42;
        Console.WriteLine(buf.Length + " " + buf[0]);
    }
}
