// 슬라이드 p14-v13-ii-order — 초기화자의 ^ 는 언제 셈하나, C# 13
using System;

class Buf
{
    int[] a = new int[4];
    public int Length
    {
        get { Console.WriteLine("  Length"); return a.Length; }
    }
    public int this[int i]
    {
        get => a[i];
        set
        {
            Console.WriteLine("  [" + i + "] = " + value);
            a[i] = value;
        }
    }
    public override string ToString() => string.Join(" ", a);
}

class Holder
{
    Buf b = new Buf();
    public Buf B { get { Console.WriteLine("  get B"); return b; } }
}

class Program
{
    static int V(int v) { Console.WriteLine("  value " + v); return v; }

    static void Main()
    {
        Console.WriteLine("init:");
        var h = new Holder { B = { [^1] = V(9), [^2] = V(8) } };
        Console.WriteLine("index plain:");
        var g = new Holder { B = { [3] = V(9) } };
        Console.WriteLine("statement:");
        h.B[^4] = V(1);
        Console.WriteLine("result: " + h.B);
    }
}
