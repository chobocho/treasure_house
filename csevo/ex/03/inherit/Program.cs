// 슬라이드 p3-v2-generic-inherit — 제네릭 형식에서 파생하기, C# 2.0
using System;
using System.Collections.Generic;

class Repo<T>
{
    protected List<T> items = new List<T>();
    public void Add(T x) { items.Add(x); }
    public int Count { get { return items.Count; } }
}

class Names : Repo<string>                // close the base
{
    public string Joined() { return string.Join("+", items.ToArray()); }
}

class Logged<T> : Repo<T>                 // stay open
{
    public void AddLogged(T x)
    {
        Console.WriteLine("add " + x);
        Add(x);
    }
}

class App
{
    static void Main()
    {
        Names n = new Names();
        n.Add("a");
        n.Add("b");
        Console.WriteLine(n.Joined());
        Logged<int> l = new Logged<int>();
        l.AddLogged(7);
        Console.WriteLine(l.Count + " " + typeof(Names).BaseType);
    }
}
