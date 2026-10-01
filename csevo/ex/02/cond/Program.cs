// 슬라이드 p2-v1-cond — 조건 연산자 ?: 의 형식, C# 1.0
using System;

class App
{
    static string Sign(int x)
    {
        return x > 0 ? "plus" : x < 0 ? "minus" : "zero"; // nested
    }

    static void Main()
    {
        bool yes = true;
        Console.WriteLine(yes ? 'a' : 'b');      // char
        Console.WriteLine(yes ? 'a' : 0);        // int: prints 97
        Console.WriteLine(yes ? 1 : 2.5);        // double
        Console.WriteLine((yes ? 1 : 2.5).GetType().Name);
        object o = yes ? (object)1 : null;       // cast one side
        Console.WriteLine(o);
        Console.WriteLine(Sign(5) + " " + Sign(-5) + " " + Sign(0));
    }
}
