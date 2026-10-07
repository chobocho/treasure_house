// 슬라이드 p15-v14-nameof — nameof 의 열린 제네릭 형식, C# 14
using System;
using System.Collections.Generic;

class A<T>
{
    public List<T> B { get; } = new();
}

class Pair<TItem, TColl> where TColl : IReadOnlyCollection<TItem>
{
    public TColl Items { get; }
}

class Program
{
    static void Main()
    {
        Console.WriteLine(nameof(List<>));
        Console.WriteLine(nameof(Dictionary<,>));
        Console.WriteLine(nameof(A<>.B));
        Console.WriteLine(nameof(A<>.B.Count));
        Console.WriteLine(nameof(Pair<,>.Items.Count)); // constraint
        Console.WriteLine(nameof(Dictionary<,>.KeyCollection));
        Console.WriteLine(typeof(Dictionary<,>).Name);  // C# 2
    }
}
