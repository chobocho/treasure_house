// 슬라이드 p15-v14-ca-null — null 인 받는 쪽과 ?.=, C# 14
using System;

class Old
{
    public static Old operator +(Old a, int d)
    {
        Console.WriteLine("  static + got " + (a ?? (object)"null"));
        return a;
    }
}

class New
{
    public int N;
    public void operator +=(int d) => N += d;
}

class Box { public New Item = new New(); }

class Program
{
    static void Main()
    {
        Old o = null;
        o += 1;                            // the operator sees null
        Box box = new Box(), none = null;
        box?.Item += 2;                    // ?.= with an instance +=
        none?.Item += 3;                   // skipped
        Console.WriteLine("  box.Item.N = " + box.Item.N);
        New n = null;
        try { n += 1; }
        catch (NullReferenceException) { Console.WriteLine("  NRE"); }
    }
}
