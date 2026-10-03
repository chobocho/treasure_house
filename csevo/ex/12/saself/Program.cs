// 슬라이드 p12-v11-sa-tself — TSelf 제약이 하는 일, C# 11.0
using System;

interface IAdd<TSelf> where TSelf : IAdd<TSelf>
{
    static abstract TSelf operator +(TSelf a, TSelf b);
}
#if BAD
interface ILoose<T>          // no "where T : ILoose<T>"
{
    static abstract T operator +(T a, T b);
}
#endif

struct Cm : IAdd<Cm>
{
    public int V;
    public static Cm operator +(Cm a, Cm b) => new Cm { V = a.V + b.V };
}

// Legal: TSelf is a convention, not a rule. Odd adds Cm values
struct Odd : IAdd<Cm>
{
    static Cm IAdd<Cm>.operator +(Cm a, Cm b) => new Cm { V = 99 };
}

class App
{
    static T Add<T>(T a, T b) where T : IAdd<T> => a + b;

    static void Main()
    {
        Console.WriteLine(Add(new Cm { V = 2 }, new Cm { V = 3 }).V);
        Console.WriteLine(
            typeof(IAdd<Cm>).IsAssignableFrom(typeof(Odd)));
    }
}
