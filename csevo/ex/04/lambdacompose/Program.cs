// 슬라이드 p4-v3-lambda-compose — 함수를 받고 함수를 돌려주기, C# 3.0
using System;

class App
{
    static Func<A, C> Compose<A, B, C>(Func<A, B> f, Func<B, C> g)
    {
        return x => g(f(x));
    }

    static void Main()
    {
        Func<int, int> inc = x => x + 1;
        Func<int, string> show = x => "<" + x + ">";
        Func<int, string> both = Compose(inc, show);
        Console.WriteLine(both(41));

        // => is right-associative: a => (b => a + b)
        Func<int, Func<int, int>> add = a => b => a + b;
        Func<int, int> add10 = add(10);
        Console.WriteLine(add10(5) + " " + add(1)(2));
    }
}
