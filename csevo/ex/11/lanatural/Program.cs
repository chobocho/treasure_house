// 슬라이드 p11-v10-lambda — 람다와 메서드 그룹의 자연 형식, C# 10.0
using System;

class App
{
    static int Twice(int x) => x * 2;
    static void Hello() => Console.WriteLine("  hello");

    static void Show(string what, Delegate d)
        => Console.WriteLine($"{what,-28}{d.GetType()}");

    static void Main()
    {
        var parse = (string s) => int.Parse(s);
        var log = (string s) => Console.WriteLine(s);
        var choose = object (bool b) => b ? 1 : "two";
        var anon = delegate (object o) { };
        var tw = Twice;                       // one method
        var hi = Hello;
        var read = Console.Read;              // one overload in Console

        Show("(string s) => int.Parse(s)", parse);
        Show("(string s) => WriteLine(s)", log);
        Show("object (bool b) => ...", choose);
        Show("delegate (object o) { }", anon);
        Show("Twice", tw);
        Show("Hello", hi);
        Show("Console.Read", read);
        Console.WriteLine($"{parse("21") + tw(10)}");
#if BAD
        var id = x => x;                      // no parameter type
        var write = Console.Write;            // many overloads
        var nothing = () => default;          // no return type
#endif
    }
}
