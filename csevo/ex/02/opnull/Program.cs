// 슬라이드 p2-v1-opnull — 오버로딩한 == 과 null 비교, C# 1.0
using System;

class Ver
{
    public int N;
    public Ver(int n) { N = n; }

    public static bool operator ==(Ver a, Ver b)
    {
        return a.N == b.N;                    // forgets about null
    }
    public static bool operator !=(Ver a, Ver b) { return !(a == b); }
    public override bool Equals(object o)
    {
        Ver v = o as Ver;
        return (object)v != null && v.N == N;
    }
    public override int GetHashCode() { return N; }
}

class App
{
    static void Main()
    {
        Ver v = null;
        Console.WriteLine("(object)v == null: " + ((object)v == null));
        Console.WriteLine("v == null:");
        Console.WriteLine(v == null);         // calls operator ==
    }
}
