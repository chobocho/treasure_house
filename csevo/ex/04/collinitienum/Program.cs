// 슬라이드 p4-v3-collinit-ienum — IEnumerable 이 없으면, C# 3.0
using System;

class Bag
{
    public int Count;
    public void Add(string s) { Count++; }
}

class App
{
    static void Main()
    {
        Bag b = new Bag { "a", "b" };
        Console.WriteLine(b.Count);
    }
}
