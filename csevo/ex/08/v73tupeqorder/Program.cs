// 슬라이드 p8-v7_3-tupleeq-order — 계산 순서와 일찍 끝내기, C# 7.3
using System;

struct V
{
    public int N;
    public V(int n) { N = n; }
    public static bool operator ==(V x, V y)
    {
        Console.Write("[" + x.N + "==" + y.N + "] ");
        return x.N == y.N;
    }
    public static bool operator !=(V x, V y) => !(x == y);
    public override bool Equals(object o) => o is V v && v.N == N;
    public override int GetHashCode() => N;
}

class App
{
    static V Get(string tag, int n)
    {
        Console.Write(tag + " ");
        return new V(n);
    }

    static void Main()
    {
        bool r = (Get("a", 1), Get("b", 2))
              == (Get("c", 9), Get("d", 2));
        Console.WriteLine("-> " + r);
        r = (Get("a", 1), Get("b", 2))
         == (Get("c", 1), Get("d", 2));
        Console.WriteLine("-> " + r);
        var nan = (double.NaN, 1);
        Console.WriteLine("nan == nan    : " + (nan == nan));
        Console.WriteLine("nan.Equals(nan): " + nan.Equals(nan));
    }
}
