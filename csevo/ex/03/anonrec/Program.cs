// 슬라이드 p3-v2-anon-recursion — 먼저 null 로 선언하기, C# 2.0
using System;

delegate int F(int n);

class App
{
    static void Main()
    {
        F fact = null;                       // declare first
        fact = delegate(int n)
        {
            return n <= 1 ? 1 : n * fact(n - 1);
        };
        Console.WriteLine(fact(5));

        F saved = fact;                      // keep the delegate
        fact = delegate(int n) { return 0; };
        Console.WriteLine(saved(5));         // inside: the new fact
    }
}
