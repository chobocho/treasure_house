// 슬라이드 p11-v10-rs-array — 배열 필드의 같음, C# 10.0
using System;
using System.Collections.Generic;

record struct Tags(string Name, int[] Ids);
record struct Box<T>(T Value);

class App
{
    static void Main()
    {
        var a = new Tags("x", new[] { 1, 2 });
        var b = new Tags("x", new[] { 1, 2 });
        Console.WriteLine(a == b);              // array by reference
        Console.WriteLine(a == b with { Ids = a.Ids });
        var n = new Box<string>(null);
        Console.WriteLine(n == new Box<string>(null));
        var l1 = new Box<List<int>>(new List<int> { 1 });
        var l2 = new Box<List<int>>(new List<int> { 1 });
        Console.WriteLine(l1 == l2);
        Console.WriteLine(a);
    }
}
