// 슬라이드 p4-v3-lambda-cache — 잡지 않은 람다는 다시 쓰인다, C# 3.0
using System;

class App
{
    static Func<int, int> Plain()
    {
        return x => x + 1;                    // captures nothing
    }

    static Func<int, int> Adder(int k)
    {
        return x => x + k;                    // captures k
    }

    static void Main()
    {
        Console.WriteLine("Plain() same object:  "
            + ReferenceEquals(Plain(), Plain()));
        Console.WriteLine("Adder(1) same object: "
            + ReferenceEquals(Adder(1), Adder(1)));
        Func<int, int> p = Plain();
        Console.WriteLine("Plain: static method=" + p.Method.IsStatic
            + ", has target=" + (p.Target != null));
        Func<int, int> a = Adder(1);
        Console.WriteLine("Adder: static method=" + a.Method.IsStatic
            + ", target is App=" + (a.Target is App));
    }
}
