// 슬라이드 p15-v14-nm-not — 여전히 안 되는 꼴, C# 14
using System;
using System.Collections.Generic;

class Outer<T>
{
    public class Inner<U> { public int Z = 1; }
}

class Program
{
    static void Main()
    {
        Console.WriteLine(nameof(Outer<>.Inner<int>));  // mixing ok
        Console.WriteLine(nameof(Outer<int>.Inner<>.Z));
#if NESTED
        Console.WriteLine(nameof(List<List<>>));
#endif
#if PARTIAL
        Console.WriteLine(nameof(Dictionary<int,>));
#endif
#if ARRAY
        Console.WriteLine(nameof(List<>[]));
#endif
#if OUTSIDE
        Console.WriteLine(List<>.Empty);
#endif
    }
}
