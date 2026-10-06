// 슬라이드 p13-v12-ce-cap — 길이를 아는 컬렉션 식과 capacity, C# 12
using System;
using System.Collections;
using System.Collections.Generic;

class Box : IEnumerable<int>
{
    readonly List<int> items;
    public Box() { Console.Write("Box() "); items = new(); }
    public Box(int capacity)
    {
        Console.Write("Box(capacity: " + capacity + ") ");
        items = new(capacity);
    }
    public void Add(int x) { items.Add(x); }
    public IEnumerator<int> GetEnumerator() => items.GetEnumerator();
    IEnumerator IEnumerable.GetEnumerator() => GetEnumerator();
}

class Program
{
    static IEnumerable<int> Two() { yield return 8; yield return 9; }

    static void Main()
    {
        int[] xs = [1, 2, 3];
        Box a = [1, 2, 3];
        Console.WriteLine();
        Box b = [0, .. xs, .. Two()];      // Two(): length unknown
        Console.WriteLine();
        var c = new Box { 1, 2, 3 };
        Console.WriteLine();
        List<int> l1 = [1, 2, 3, 4, 5];
        var l2 = new List<int> { 1, 2, 3, 4, 5 };
        Console.WriteLine(l1.Capacity + " " + l2.Capacity);
    }
}
