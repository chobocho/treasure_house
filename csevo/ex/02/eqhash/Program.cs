// 슬라이드 p2-v1-eqhash — Equals 와 GetHashCode 는 짝, C# 1.0
using System;

class Tag
{
    public string Name;
    public Tag(string name) { Name = name; }
    public override bool Equals(object o)       // GetHashCode missing
    {
        Tag t = o as Tag;
        return t != null && t.Name == Name;
    }
}

class Pair
{
    public int A;
    public Pair(int a) { A = a; }
    public static bool operator ==(Pair l, Pair r)
    {
        return l.A == r.A;
    }
    public static bool operator !=(Pair l, Pair r) { return !(l == r); }
}

class App
{
    static void Main()
    {
        Console.WriteLine(new Tag("x").Equals(new Tag("x")));
        Pair p = new Pair(1), q = new Pair(1);
        Console.WriteLine(p == q);
    }
}
