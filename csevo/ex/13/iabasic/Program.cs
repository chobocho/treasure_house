// 슬라이드 p13-v12-inline — 인라인 배열, C# 12.0
using System;
using System.Runtime.CompilerServices;

[InlineArray(10)]
public struct Buffer        // the whats-new example
{
    private int _element0;
}

class App
{
    static void Main()
    {
        var buffer = new Buffer();
        for (int i = 0; i < 10; i++)
        {
            buffer[i] = i;
        }
        foreach (var i in buffer)
        {
            Console.Write(i + " ");
        }
        Console.WriteLine();
        Span<int> s = buffer;      // inline array conversion
        s.Reverse();
        Console.WriteLine(buffer[0] + " " + s.Length);
    }
}
