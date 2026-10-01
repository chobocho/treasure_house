// 슬라이드 p4-v3-query-pattern — Where·Select 만 가진 형식, C# 3.0
using System;

delegate R Fn<T, R>(T arg);          // not even System.Func

class Box<T>
{
    public readonly T Value;
    public Box(T v) { Value = v; }

    public Box<U> Select<U>(Fn<T, U> f)
    {
        Console.WriteLine("  Box.Select");
        return new Box<U>(f(Value));
    }

    public Box<T> Where(Fn<T, bool> p)
    {
        Console.WriteLine("  Box.Where");
        return p(Value) ? this : new Box<T>(default(T));
    }
}

class Program
{
    static void Main()
    {
        Box<int> b = new Box<int>(20);
        Box<string> r = from x in b
                        where x > 10
                        select "value " + x;
        Console.WriteLine(r.Value);
    }
}
