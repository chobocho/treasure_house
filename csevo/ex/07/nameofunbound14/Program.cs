// 슬라이드 p7-v6-nameof-unbound14 — nameof(List<>), C# 14.0
using System;
using System.Collections.Generic;

class Box<T> where T : IComparable<T>
{
    public T Value = default(T);
}

class App
{
    static void Main()
    {
        Console.WriteLine(nameof(List<>));
        Console.WriteLine(nameof(Dictionary<,>));
        Console.WriteLine(nameof(List<>.Count));     // member chain
        Console.WriteLine(nameof(Box<>));            // no dummy T
        Console.WriteLine(nameof(Box<>.Value));
        Console.WriteLine(nameof(Box<int>.Value));   // C# 6 way
    }
}
