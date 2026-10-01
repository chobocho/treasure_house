// 슬라이드 p4-v3-lambda-forms — 람다의 여러 꼴, C# 3.0
using System;

class App
{
    static void Main()
    {
        Func<int, int> a = x => x + 1;                 // implicit
        Func<int, int> b = x => { return x + 1; };     // block
        Func<int, int> c = (int x) => x + 1;           // explicit
        Func<int, int> d = (int x) => { return x + 1; }; // both
        Func<int, int, int> e = (x, y) => x * y;       // two
        Action f = () => Console.WriteLine("no parameters");
        Func<int, int> g = delegate(int x) { return x + 1; }; // C# 2

        Console.WriteLine(a(1) + b(1) + c(1) + d(1) + g(1)
            + " " + e(6, 7));
        f();
    }
}
