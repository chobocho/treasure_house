// 슬라이드 p11-v10-rs-hash — record struct 의 GetHashCode, C# 10.0
using System;
using System.Collections.Generic;

record struct Meters(int Value);
record struct Seconds(int Value);
record struct Pair(int A, int B);

class App
{
    static void Main()
    {
        // int hashes are the value itself: safe to print
        Console.WriteLine(new Meters(5).GetHashCode());
        Console.WriteLine(new Seconds(5).GetHashCode());
        Console.WriteLine(new Pair(1, 2).GetHashCode());
        Console.WriteLine(new Pair(2, 1).GetHashCode());
        Console.WriteLine(1 * -1521134295 + 2);
        var set = new HashSet<Meters> { new Meters(5), new Meters(5) };
        Console.WriteLine(set.Count);
    }
}
