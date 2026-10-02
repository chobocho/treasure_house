// 슬라이드 p7-v6-nameof-kinds — 마지막 식별자 하나, C# 6.0
using System;
using System.Collections.Generic;
using Text = System.Text.StringBuilder;

class Outer
{
    public class Inner { }
    public void Run<T>(T x) { }
    public int Count { get { return 0; } }
}

class App
{
    static void Main()
    {
        int @class = 1;
        Console.WriteLine(nameof(System));          // namespace
        Console.WriteLine(nameof(System.Collections.Generic));
        Console.WriteLine(nameof(List<int>));       // generic type
        Console.WriteLine(nameof(Dictionary<string, Outer>));
        Console.WriteLine(nameof(Text));            // alias
        Console.WriteLine(nameof(Outer.Inner));     // nested type
        Console.WriteLine(nameof(Outer.Run));       // generic method
        Console.WriteLine(nameof(Outer.Count));     // instance prop
        Console.WriteLine(nameof(string.Length));
        Console.WriteLine(nameof(int.MaxValue));    // keyword.member
        Console.WriteLine(nameof(@class));          // @ removed
        Console.WriteLine(nameof(Console.Out.WriteLine)); // overloads
        Console.WriteLine(@class);
    }
}
