// 슬라이드 p4-v3-collinit-add — IEnumerable + Add 면 무엇이든, C# 3.0
using System;
using System.Collections;

class Bag : IEnumerable
{
    public void Add(string s)
    {
        Console.WriteLine("Add(string " + s + ")");
    }
    public void Add(int n) { Console.WriteLine("Add(int " + n + ")"); }
    public void Add(string k, int v)
    {
        Console.WriteLine("Add(" + k + ", " + v + ")");
    }

    // only required to exist; the initializer never calls it
    public IEnumerator GetEnumerator()
    {
        throw new NotImplementedException();
    }
}

class App
{
    static void Main()
    {
        Bag b = new Bag { "a", 2, { "c", 3 }, 'd'.ToString() };
        Console.WriteLine(b != null);
    }
}
